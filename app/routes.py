import os  # Voor bestandspaden en mapbeheer
import json
from pathlib import Path
from datetime import datetime  # Voor datum- en tijdstempels
from flask import Blueprint, render_template, request, session, redirect, url_for, flash, current_app, jsonify
from werkzeug.utils import secure_filename  # Voor veilige bestandsnamen bij uploads
from app import db  # SQLAlchemy-instantie
from app.models import User, Recipe, Review, Transaction, Feedback  # Je databasemodellen
from app.forms import RecipeForm, ReviewForm, EditProfileForm, ContactForm, ChefProfileForm
from app.dropdowns import get_allergens, get_categories, get_origins
from sqlalchemy import and_, or_, func
from app.filters import apply_filters
from app.sort import apply_sorting
from app.zoekbalk import apply_search
from flask_mail import Mail, Message
from app.check_and_notify_chef import check_and_notify_chef
from app import mail
from app.forms import UserForm, LoginForm, RecipeForm  # Je Flask-WTF-formulieren
from flask_wtf.file import FileAllowed

main = Blueprint('main', __name__)
chatbot = Blueprint('chatbot', __name__)


@main.route('/')
def index():
    return render_template('index.html')


@main.route('/register', methods=['GET', 'POST'])
def register():
    form = UserForm()
    
    # Gebruik ingredienten direct vanuit ingredients.py
    form.allergies.choices = [(allergy, allergy) for allergy in get_allergens()]
    form.favorite_origins.choices = [(origin, origin) for origin in get_origins()]
    
    if form.validate_on_submit():
        print("Form is submitted")
        print(f"E-mail: {form.email.data}")

        # Haal de waarde van is_chef direct op uit de POST-gegevens
        is_chef_value = request.form.get('is_chef')
        print(f"Received is_chef value: {is_chef_value}")
        is_chef = True if is_chef_value == 'true' else False  # Converteer correct naar boolean

        # Check if the user already exists
        if User.query.filter_by(email=form.email.data).first():
            print(f"The email {form.email.data} is already in use.")
            flash('This email is already in use, pick another one or login', 'danger')
            return redirect(url_for('main.register'))
        
        favorite_ingredients = form.favorite_ingredients.data.split(',') if form.favorite_ingredients.data else []
        profile_picture_path = None
        if is_chef and form.profile_picture.data:
            if hasattr(form.profile_picture.data, 'filename') and form.profile_picture.data.filename:
                try:
                    upload_folder = os.path.join(current_app.root_path, 'static/images')
                    os.makedirs(upload_folder, exist_ok=True)

                    image_file = form.profile_picture.data
                    filename = secure_filename(image_file.filename)
                    file_path = os.path.join(upload_folder, filename)
                    image_file.save(file_path)
                    profile_picture_path = f'images/{filename}'  # Sla de URL van de foto op
                except Exception as e:
                    flash(f"Error saving profile picture: {e}", 'danger')
            else:
                flash('No valid file uploaded for profile picture.', 'warning')

        # Maak nieuwe gebruiker aan
        preferences = {
            "allergies": form.allergies.data or [],
            "favorite_origins": form.favorite_origins.data or [],
            "favorite_ingredients": favorite_ingredients,
        }
        new_user = User(
            email=form.email.data,
            name=form.name.data,
            date_of_birth=form.date_of_birth.data,
            street=form.street.data,
            housenr=form.housenr.data,
            postalcode=form.postalcode.data,
            city=form.city.data,
            country=form.country.data,
            telephonenr=form.telephonenr.data,
            is_chef=is_chef,
            preferences=preferences,
            profile_picture=profile_picture_path if is_chef else None,  # Profielfoto alleen voor chefs
            chef_description=form.chef_description.data if is_chef else None  # Beschrijving alleen voor chefs
        )

        # Voeg nieuwe gebruiker toe aan de database
        print("User is being added to the database...")
        db.session.add(new_user)
        db.session.commit()

        # Flash een succesbericht
        flash('You are registered successfully', 'success')

        # Redirect naar de login pagina
        print("Redirecting to the login page...")
        return redirect(url_for('main.login'))

    print("Form not submitted successfully")
    return render_template('register.html', form=form)


@main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        user = User.query.filter_by(email=email).first()
        if user:
            # Sla e-mail en rol op in de session
            session['email'] = user.email
            session['role'] = 'chef' if user.is_chef else 'customer'
            flash(f'Logged in as {user.email}', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid email. Please try again.', 'danger')
    return render_template('login.html', form=form)

    
@main.route('/dashboard')
def dashboard():
    if 'email' not in session:
        flash('You need to log in first.', 'danger')
        return redirect(url_for('main.login'))

    # Huidige gebruiker ophalen
    user = User.query.filter_by(email=session['email']).first()
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('main.login'))

    # Haal gegevens op voor dropdowns
    categories = get_categories()
    origins = get_origins()
    allergens = get_allergens()

    search_query = request.args.get('search', '')
    max_price_query = db.session.query(func.max(Recipe.price)).scalar()
    max_price = max_price_query if max_price_query is not None else 100.0

    # Initialiseer filters
    allergies_input = request.args.get('allergies', "")
    allergies_list = [a.lower().strip() for a in allergies_input.split(",") if a]
    filters = {
        'ingredients': request.args.get('ingredients', '[]'),  # JSON string van ingrediënten
        'min_price': request.args.get('min_price', 0),
        'max_price': request.args.get('max_price', max_price),  # Gebruik max_price als standaard
        'allergies': allergies_list,  # Zorg voor een genormaliseerde lijst
        'min_rating': request.args.get('min_rating'),
        'duration': request.args.get('duration'),
        'category': request.args.get('category'),
        'origin': request.args.get('origin'),
    }

    # Gebruik standaard sortering
    sort_by = request.args.get('sort_by', 'recommended' if not user.is_chef else 'price_quality')

    # Query starten
    query = Recipe.query

    # Filters toepassen
    query = apply_filters(query, filters)

    query = apply_search(query, search_query)

    # Sorteerfunctie toepassen met voorkeuren
    preferences = user.preferences or {'favorite_ingredients': [], 'favorite_origins': []}
    query = apply_sorting(query, sort_by, preferences=preferences)

    # Gefilterde recepten ophalen
    recipes = query.all()

    # Verwerk recepten en voeg extra gegevens toe
    recipe_data = []
    user_favorites = user.favorites or []

    for recipe in recipes:
        # Gemiddelde beoordeling berekenen
        avg_rating = (
            db.session.query(func.avg(Review.rating))
            .filter(Review.recipename == recipe.recipename)
            .scalar()
        )
        avg_rating = round(avg_rating, 1) if avg_rating else None

        # Filteren op minimale beoordeling
        if filters.get('min_rating'):
            try:
                min_rating = float(filters['min_rating'])
                if avg_rating is None or avg_rating < min_rating:
                    continue  # Skip dit recept als het niet voldoet
            except ValueError:
                flash("Invalid minimum rating value.", "danger")

        # Ingrediëntenlijst verwerken
        ingredients_list = []
        if recipe.ingredients:
            for ingredient, details in recipe.ingredients.items():
                ingredients_list.append({
                    'quantity': details.get('quantity', ''),
                    'unit': details.get('unit', ''),
                    'ingredient': ingredient
                })

        # Allergieën verwerken
        allergies = recipe.allergiesrec.split(", ") if recipe.allergiesrec else []
        is_liked = user.is_favorite(recipe.recipename, recipe.chef_email)

        # Voeg alle verwerkte gegevens toe aan de lijst
        recipe_data.append({
            'recipe': recipe,
            'avg_rating': avg_rating,
            'ingredients_list': ingredients_list,
            'allergies': allergies,  # Voeg 'allergies' expliciet toe
            'is_liked': is_liked  # Include the accurate liked state
        })
    
    

    # Render de template met de nodige gegevens
    return render_template(
        'dashboard.html',
        user=user,
        recipe_data=recipe_data,
        categories=categories,
        origins=origins,
        allergens=allergens,
        sort_by=sort_by,
        user_favorites=user_favorites,
        max_price=max_price,
        filters=filters  # Geef filters door voor persistentie
    )



@main.route('/logout', methods=['GET'])
def logout():
    print("Logout route is reached")  # Dit verschijnt in je terminal voor debugging
    # Verwijder de email uit de sessie om de gebruiker uit te loggen
    if 'email' in session:
        session.pop('email', None)
        flash('You have been logged out successfully.', 'info')
        print("User session cleared, redirecting to index")

    # Redirect naar de homepage of een andere pagina na uitloggen
    return redirect(url_for('main.index'))

@main.route('/recipes', methods=['GET'])
def list_recipes():
    # Haal alle recepten op uit de database
    recipes = Recipe.query.all()
    
    # Render de template en geef de recepten mee
    return render_template('listing.html', recipes=recipes)



@main.route('/add_recipe', methods=['GET', 'POST'])
def add_recipe():
    if 'email' not in session or session.get('role') != 'chef':
        flash('You need to log in as a chef to add recipes.', 'danger')
        return redirect(url_for('main.login'))

    form = RecipeForm()

    # Gebruik directe import van allergenen, origins en categorieën
    allergens = get_allergens()
    categories = get_categories()
    origins = get_origins()

    if form.validate_on_submit():
        try:
            # Zorg ervoor dat de uploadmap bestaat
            upload_folder = Path(current_app.root_path) / 'static' / 'images'
            upload_folder.mkdir(parents=True, exist_ok=True)

            # Verwerk de afbeelding
            image_file = form.image.data
            filename = secure_filename(image_file.filename) if image_file else None
            relative_path = None

            if filename:
                # Verwerk de geüploade afbeelding
                upload_folder = os.path.join(current_app.root_path, 'static/images')
                os.makedirs(upload_folder, exist_ok=True)  # Zorg dat de map bestaat

                # Save de afbeelding
                file_path = os.path.join(upload_folder, filename)
                file_path = file_path.replace("C:", "").replace("\\", "/")  # Remove "C:" and normalize to "/"
                image_file.save(file_path)

                # Gebruik altijd relatieve paden voor de database
                relative_path = f'images/{filename}'
            else:
                # Gebruik een default afbeelding als er geen bestand is geüpload
                relative_path = 'images/default_recipe_image.jpeg'

            # Haal ingrediënten, hoeveelheden en eenheden op uit het formulier
            ingredients = request.form.getlist('ingredients[]')
            quantities = request.form.getlist('quantities[]')
            units = request.form.getlist('units[]')

            # Maak een dictionary voor de ingrediënten
            ingredient_dict = {}
            for ingredient, quantity, unit in zip(ingredients, quantities, units):
                if ingredient and quantity and unit:  # Zorg dat alle velden zijn ingevuld
                    ingredient_dict[ingredient.strip()] = {
                        "quantity": quantity.strip(),
                        "unit": unit.strip()
                    }

            # Haal geselecteerde allergenen op uit de dropdown
            selected_allergens = request.form.getlist('allergiesrec[]')
            allergens_string = ', '.join(selected_allergens)  # Opslaan als een door komma's gescheiden string

            # Haal bereidingsstappen op en combineer ze in één string, gescheiden door pipes
            preparation_steps = request.form.getlist('preparation_steps[]')
            preparation_instructions = '|'.join([step.strip() for step in preparation_steps if step.strip()])

            # Haal de naam van de chef op
            chef = User.query.filter_by(email=session['email']).first()
            chef_name = chef.name if chef else None

            # Maak een nieuw receptobject
            new_recipe = Recipe(
                recipename=form.recipename.data,
                chef_email=session['email'],
                chef_name=chef_name,  # Naam van de chef automatisch ophalen
                description=form.description.data,
                duration=form.duration.data,
                price=form.price.data,
                ingredients=ingredient_dict,
                allergiesrec=allergens_string,  # Opslaan als string
                image=relative_path,
                origin=form.origin.data,  # Herkomstveld toevoegen
                category=form.category.data,  # Categorieveld toevoegen
                preparation=preparation_instructions  # Bereidingswijze als een lange string
            )

            # Voeg toe aan de database en sla op
            db.session.add(new_recipe)
            db.session.commit()
            flash('Recipe added successfully!', 'success')
            return redirect(url_for('main.my_uploads'))

        except Exception as e:
            # Rol de wijzigingen terug bij een fout
            db.session.rollback()
            flash(f"Error saving recipe: {e}", 'danger')
            print("Error:", str(e))

    # Render de template en geef de allergenen, ingrediënten, en formulier door
    return render_template(
        'add_recipe.html',
        form=form,
        allergens=allergens,
        categories=categories,
        origins=origins
    )



@main.route('/my_recipes')
def my_recipes():
    if 'email' not in session or session.get('role') != 'customer':
        flash('You need to log in as a customer to access this page.', 'danger')
        return redirect(url_for('main.login'))

    # Haal de huidige gebruiker op
    user_email = session['email']

    # Haal de transacties op waar deze gebruiker de koper is (customer)
    transactions = Transaction.query.filter_by(consumer_email=user_email).all()

    # Haal de recepten op die bij deze transacties horen, inclusief de chefnaam
    purchased_recipes = []
    for transaction in transactions:
        recipe = Recipe.query.filter_by(recipename=transaction.recipename, chef_email=transaction.chef_email).first()
        if recipe:
            # Ingrediënten verwerken (uit de dictionary in plaats van JSON)
            ingredients_list = []
            if recipe.ingredients:
                try:
                    # Loop door de ingrediënten dictionary
                    for ingredient, details in recipe.ingredients.items():
                        # Voeg de hoeveelheid, maateenheid en ingrediënt toe aan de lijst
                        quantity = details['quantity']
                        unit = details.get('unit', '')  # Als er geen eenheid is, gebruik een lege string
                        ingredients_list.append(f"{quantity} {unit} of {ingredient}")
                except KeyError:
                    ingredients_list = ["Invalid ingredient format"]

            chef = User.query.filter_by(email=recipe.chef_email).first()
            purchased_recipes.append({
                "recipename": recipe.recipename,
                "chef_name": chef.name if chef else "Unknown",
                "description": recipe.description,
                "duration": recipe.duration,
                "price": recipe.price,
                "ingredients_list": ingredients_list,  # Geprocessed ingredientenlijst
                "allergiesrec": recipe.allergiesrec,
                "image": recipe.image
            })

    return render_template('my_recipes.html', recipes=purchased_recipes)



@main.route('/recipe/<recipename>', methods=['GET'])
def recipe_detail(recipename):
    # Haal het recept op uit de database
    recipe = Recipe.query.filter_by(recipename=recipename).first()
    if not recipe:
        flash('Recipe not found.', 'danger')
        return redirect(url_for('main.dashboard'))

    user_email = session.get('email')
    user_review = Review.query.filter_by(recipename=recipename, consumer_email=user_email).first()

    # Ingrediënten verwerken uit dictionary voor detailweergave
    ingredients_list = []
    if recipe.ingredients:
        try:
            # Loop door de ingrediënten dictionary
            for ingredient, details in recipe.ingredients.items():
                # Haal de hoeveelheid, maateenheid en het ingrediënt op
                quantity = details['quantity']
                unit = details.get('unit', '')  # Als er geen eenheid is, gebruik een lege string
                ingredients_list.append({
                    'quantity': quantity,
                    'unit': unit,
                    'ingredient': ingredient
                })
        except KeyError:
            ingredients_list = [{"quantity": "", "unit": "", "ingredient": "Invalid ingredient format"}]

    return render_template(
        'recipe_detail.html',
        recipe=recipe,
        user_review=user_review,
        ingredients_list=ingredients_list  # De lijst van ingredienten als dictionaries
    )




@main.route('/my_uploads')
def my_uploads():
    if 'email' not in session or session.get('role') != 'chef':
        flash('You need to log in as a chef to access this page.', 'danger')
        return redirect(url_for('main.login'))
    
    recipes = Recipe.query.filter_by(chef_email=session['email']).all()

    chef_email = session['email']
    uploads = Recipe.query.filter_by(chef_email=chef_email).all()

    # Berekeningen
    uploads_data = []
    total_revenue = 0
    revenue_data = []
    for recipe in uploads:
        # Parse ingrediënten
        ingredients_list = []
        if recipe.ingredients:
            try:
                for ingredient, details in recipe.ingredients.items():
                    quantity = details.get("quantity", "")
                    unit = details.get("unit", "")
                    ingredients_list.append(f"{quantity} {unit} of {ingredient}")
            except KeyError:
                ingredients_list = ["Invalid ingredient format"]

        # Bereken gemiddelde beoordeling
        avg_rating = (
            db.session.query(db.func.avg(Review.rating))
            .filter(Review.recipename == recipe.recipename)
            .scalar()
        )
        avg_rating = round(avg_rating, 1) if avg_rating else None

        # Bereken totale omzet per gerecht
        total_recipe_revenue = (
            db.session.query(db.func.sum(Transaction.price))
            .filter(Transaction.recipename == recipe.recipename, Transaction.chef_email == chef_email)
            .scalar()
        ) or 0
        total_revenue += total_recipe_revenue

        revenue_data.append({
            'recipename': recipe.recipename,
            'total_revenue': total_recipe_revenue
        })

        uploads_data.append({
            'recipe': recipe,
            'ingredients_list': ingredients_list,
            'avg_rating': avg_rating,
            'allergies': recipe.allergiesrec  # Voeg allergies toe
        })

    # Sorteer de recepten op basis van omzet en haal de top 5 bestverkochte recepten
    revenue_data = sorted(revenue_data, key=lambda x: x['total_revenue'], reverse=True)[:5]

    # Bereken overall average rating
    overall_avg_rating = (
        db.session.query(db.func.avg(Review.rating))
        .filter(Review.chef_email == chef_email)
        .scalar()
    )
    overall_avg_rating = round(overall_avg_rating, 1) if overall_avg_rating else 0

    return render_template('my_uploads.html',
                           uploads_data=uploads_data,
                           overall_avg_rating=overall_avg_rating,
                           total_revenue=total_revenue,
                           revenue_data=revenue_data, recipes=recipes)



@main.route('/buy_recipe/<recipename>', methods=['GET', 'POST'])
def buy_recipe(recipename):
    # Fetch recipe from the database
    recipe = Recipe.query.filter_by(recipename=recipename).first()

    if recipe is None:
        flash('Recipe not found', 'danger')
        return redirect(url_for('main.dashboard'))

    # Fetch chef details from the User model
    chef = User.query.filter_by(email=recipe.chef_email).first()

    # Calculate chef's average rating
    chef_reviews = Review.query.filter_by(chef_email=chef.email).all()
    chef_avg_rating = (
        round(sum(review.rating for review in chef_reviews) / len(chef_reviews), 1) if chef_reviews else None
    )

    # Calculate recipe's average rating
    recipe_reviews = Review.query.filter_by(recipename=recipename).all()
    recipe_avg_rating = (
        round(sum(review.rating for review in recipe_reviews) / len(recipe_reviews), 1) if recipe_reviews else None
    )

    # Calculate total recipes sold by the chef
    total_recipes_sold = Transaction.query.filter_by(chef_email=chef.email).count()

    # Ingrediënten als JSON voorbereiden
    ingredients_to_match = [{'ingredient': ing} for ing in recipe.ingredients.keys()]

    # Gerelateerde recepten ophalen
    related_recipes = Recipe.query.filter(
        (Recipe.origin == recipe.origin) | 
        (Recipe.ingredients.contains(ingredients_to_match))
    ).filter(Recipe.recipename != recipename).limit(4).all()

    # Check if user is logged in
    if 'email' not in session:
        flash('You need to be logged in to buy a recipe.', 'danger')
        return redirect(url_for('main.login'))

    # Process ingredients
    ingredients_list = []
    if recipe.ingredients:
        try:
            for ingredient, details in recipe.ingredients.items():
                ingredients_list.append({
                    'quantity': details['quantity'],
                    'unit': details.get('unit', ''),
                    'ingredient': ingredient
                })
        except KeyError:
            ingredients_list = ["Invalid ingredient format"]

    # Fetch reviews for the recipe
    reviews = Review.query.filter_by(recipename=recipename, chef_email=recipe.chef_email).all()

    # Handle POST request for purchase
    if request.method == 'POST':
        user_email = session['email']
        chef_email = recipe.chef_email

        existing_transaction = Transaction.query.filter_by(
            consumer_email=user_email,
            recipename=recipename
        ).first()

        if existing_transaction:
            flash('You have already purchased this recipe.', 'warning')
            return redirect(url_for('main.dashboard'))

        # Create the transaction
        transaction = Transaction(
            transactiondate=datetime.now(),
            price=recipe.price,
            consumer_email=user_email,
            chef_email=chef_email,
            recipename=recipename
        )
        db.session.add(transaction)
        db.session.commit()

        # Check if chef should be notified
        check_and_notify_chef(chef_email, recipename)

        flash('Recipe purchased successfully!', 'success')
        return redirect(url_for('main.my_recipes'))

    return render_template(
        'buy_recipe.html',
        recipe=recipe,
        chef=chef,  # Pass the chef object to the template
        chef_avg_rating=chef_avg_rating,  # Pass the average rating to the template
        total_recipes_sold=total_recipes_sold,  # Pass the total recipes sold
        ingredients_list=ingredients_list,
        reviews=reviews,
        related_recipes=related_recipes,
        recipe_avg_rating=recipe_avg_rating  # Pass the recipe's average rating to the template
    )


@main.route('/add_review/<recipename>', methods=['GET', 'POST'])
def add_review(recipename):
    # Zorg dat de gebruiker is ingelogd
    if 'email' not in session:
        flash('You need to log in to add a review.', 'danger')
        return redirect(url_for('main.login'))

    # Haal het recept op
    recipe = Recipe.query.filter_by(recipename=recipename).first()
    if not recipe:
        flash('Recipe not found.', 'danger')
        return redirect(url_for('main.my_recipes'))

    # Controleer of de transactie bestaat
    transaction = Transaction.query.filter_by(
        recipename=recipename,
        consumer_email=session['email']
    ).first()

    if not transaction:
        flash('No transaction found for this recipe.', 'danger')
        return redirect(url_for('main.my_recipes'))

    # Haal de chef_email uit het recept
    chef_email = recipe.chef_email

    if request.method == 'POST':
        # Haal gegevens uit het formulier
        rating = request.form.get('rating')
        comment = request.form.get('comment')

        # Controleer of alle velden zijn ingevuld
        if not rating or not comment:
            flash('All fields are required.', 'danger')
            return redirect(url_for('main.add_review', recipename=recipename))

        # Maak een nieuwe review aan
        try:
            new_review = Review(
                comment=comment,
                rating=int(rating),
                consumer_email=session['email'],
                recipename=recipename,
                chef_email=chef_email,  # Voeg de chef_email toe
                transactionid=transaction.transactionid
            )
            db.session.add(new_review)
            db.session.commit()

            flash('Review submitted successfully!', 'success')
            return redirect(url_for('main.my_recipes', recipename=recipename))
        except Exception as e:
            db.session.rollback()
            flash(f"Error submitting review: {e}", 'danger')

    return render_template('add_review.html', recipe=recipe, transaction=transaction)


@main.route('/edit_recipe/<recipename>', methods=['GET', 'POST'])
def edit_recipe(recipename):
    recipe = Recipe.query.filter_by(recipename=recipename).first()
    
    if not recipe:
        flash('Recipe not found.', 'danger')
        return redirect(url_for('main.my_uploads'))

    ingredients = recipe.ingredients if recipe.ingredients else {}
    form = RecipeForm(obj=recipe)

    # Haal dropdownwaarden op
    categories = get_categories()
    origins = get_origins()
    allergens = get_allergens()

    if form.validate_on_submit():
        try:
            recipe.recipename = form.recipename.data
            recipe.description = form.description.data
            recipe.duration = form.duration.data
            recipe.price = form.price.data
            recipe.origin = form.origin.data
            recipe.category = form.category.data

            # Update allergies
            selected_allergens = request.form.getlist('allergiesrec[]')
            recipe.allergiesrec = ', '.join(selected_allergens)

            # Update preparation steps
            preparation_steps = request.form.getlist('preparation_steps[]')
            recipe.preparation = '|'.join([step.strip() for step in preparation_steps if step.strip()])

            # Update ingredients
            ingredient_names = request.form.getlist('ingredients[]')
            ingredient_quantities = request.form.getlist('quantities[]')
            ingredient_units = request.form.getlist('units[]')

            updated_ingredients = {}
            for name, quantity, unit in zip(ingredient_names, ingredient_quantities, ingredient_units):
                if name and quantity and unit:
                    updated_ingredients[name.strip()] = {
                        "quantity": quantity.strip(),
                        "unit": unit.strip()
                    }
            recipe.ingredients = updated_ingredients

            # Update image
            if form.image.data:
                image_file = form.image.data
                filename = secure_filename(image_file.filename)
                upload_folder = os.path.join(current_app.root_path, 'static/images')
                os.makedirs(upload_folder, exist_ok=True)
                file_path = os.path.join(upload_folder, filename)
                file_path = file_path.replace("C:", "").replace("\\", "/")
                image_file.save(file_path)
                recipe.image = f'images/{filename}'
                
            db.session.commit()
            flash('Recipe updated successfully!', 'success')
            return redirect(url_for('main.my_uploads'))

        except Exception as e:
            db.session.rollback()
            flash(f"Error updating recipe: {e}", 'danger')

    return render_template(
        'edit_recipe.html',
        form=form,
        recipe=recipe,
        ingredients=ingredients,
        categories=categories,
        origins=origins,
        allergens=allergens
    )


@main.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    # Haal de gebruiker op basis van sessie-email
    user = User.query.filter_by(email=session.get('email')).first()

    # Controleer of de gebruiker is ingelogd
    if not user:
        flash('Please log in to access your profile.', 'danger')
        return redirect(url_for('main.login'))

    # Maak het formulier en vul het met huidige gebruikersdata
    form = EditProfileForm(obj=user)

    # Dynamische keuzes instellen
    form.allergies.choices = [(a, a) for a in get_allergens()]
    form.favorite_origins.choices = [(o, o) for o in get_origins()]

    # Voorkeuren ophalen uit de database
    preferences = user.preferences or {
        'allergies': [],
        'favorite_ingredients': [],
        'favorite_origins': []
    }

    # Vul het formulier met bestaande gegevens
    if request.method == 'GET':
        form.allergies.data = preferences.get('allergies', [])
        form.favorite_ingredients.data = '\n'.join(preferences.get('favorite_ingredients', []))  # Opslaan als tekst
        form.favorite_origins.data = preferences.get('favorite_origins', [])

    # Verwerk formulierindiening
    if form.validate_on_submit():
        try:
            # Persoonlijke gegevens bijwerken
            user.name = form.name.data or user.name
            user.date_of_birth = form.date_of_birth.data or user.date_of_birth
            user.street = form.street.data or user.street
            user.housenr = form.housenr.data or user.housenr
            user.postalcode = form.postalcode.data or user.postalcode
            user.city = form.city.data or user.city
            user.country = form.country.data or user.country
            user.telephonenr = form.telephonenr.data or user.telephonenr

            # Ingrediënten verwerken (gescheiden door nieuwe regels)
            new_ingredients = [ingredient.strip() for ingredient in form.favorite_ingredients.data.split('\n') if ingredient.strip()]

            # Voorkeuren bijwerken
            updated_preferences = {
                'allergies': form.allergies.data,
                'favorite_ingredients': new_ingredients,
                'favorite_origins': form.favorite_origins.data
            }
            user.preferences = updated_preferences

            # Opslaan in de database
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('main.dashboard'))

        except Exception as e:
            db.session.rollback()
            flash(f"Error updating profile: {e}", 'danger')

    return render_template('edit_profile.html', form=form, user=user)



@main.route('/recipe_reviews/<recipename>')
def recipe_reviews(recipename):
    from_my_uploads = request.args.get('from_my_uploads', False)

    # Fetch recipe from the database
    recipe = Recipe.query.filter_by(recipename=recipename).first()

    if recipe is None:
        flash('Recipe not found', 'danger')
        return redirect(url_for('main.dashboard'))

    # Fetch chef details from the User model
    chef = User.query.filter_by(email=recipe.chef_email).first()

    # Calculate chef's average rating
    chef_reviews = Review.query.filter_by(chef_email=chef.email).all()
    chef_avg_rating = (
        round(sum(review.rating for review in chef_reviews) / len(chef_reviews), 1) if chef_reviews else None
    )

    # Calculate total recipes sold by the chef
    total_recipes_sold = Transaction.query.filter_by(chef_email=chef.email).count()

    reviews = Review.query.filter_by(recipename=recipename, chef_email=recipe.chef_email).all()

    # Bereken gemiddelde beoordeling handmatig
    avg_rating_query = db.session.query(func.avg(Review.rating)).filter(Review.recipename == recipe.recipename).scalar()
    avg_rating = round(avg_rating_query, 1) if avg_rating_query else None


    # Ingrediënten als JSON voorbereiden
    ingredients_to_match = [{'ingredient': ing} for ing in recipe.ingredients.keys()]

    # Gerelateerde recepten ophalen
    related_recipes = Recipe.query.filter(
        (Recipe.origin == recipe.origin) | 
        (Recipe.ingredients.contains(ingredients_to_match))
    ).filter(Recipe.recipename != recipename).limit(4).all()

    # Process ingredients
    ingredients_list = []
    if recipe.ingredients:
        try:
            for ingredient, details in recipe.ingredients.items():
                ingredients_list.append({
                    'quantity': details['quantity'],
                    'unit': details.get('unit', ''),
                    'ingredient': ingredient
                })
        except KeyError:
            ingredients_list = ["Invalid ingredient format"]

    # Fetch reviews for the recipe
    reviews = Review.query.filter_by(recipename=recipename, chef_email=recipe.chef_email).all()

    return render_template(
        'recipe_reviews.html',
        recipe=recipe,
        chef=chef,
        chef_avg_rating=chef_avg_rating,
        total_recipes_sold=total_recipes_sold,
        ingredients_list=ingredients_list,
        reviews=reviews,
        related_recipes=related_recipes,
        avg_rating=avg_rating,  # Pass the recipe's average rating
        from_my_uploads=from_my_uploads  # Doorgeven aan de template

    )

from flask import Blueprint, render_template, request, jsonify
from .responses import get_response  # Importeer de get_response functie

@chatbot.route('/chat', methods=['GET', 'POST'])
def chat():
    if request.method == 'POST':
        try:
            # Haal het gebruikersbericht op
            user_message = request.json.get('message', '').strip()
            print(f"User message: {user_message}")  # Debugging log

            # Haal een reactie op uit responses.py
            response = get_response(user_message)
            print(f"Chatbot response: {response}")  # Debugging log

            return jsonify({"response": response}), 200
        except Exception as e:
            print(f"Error in chatbot: {e}")
            return jsonify({"response": "There was an error processing your request. Please try again later."}), 500

    # Render de chatbot-template bij een GET-verzoek
    return render_template('chatbot.html')

from flask_mail import Message

@main.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        try:
            # Collect form data
            name = form.name.data
            email = form.email.data
            subject = form.subject.data
            message = form.message.data
            is_public = form.is_public.data  # Retrieve the checkbox value

            # Save feedback to the database
            new_feedback = Feedback(
                name=name,
                email=email,
                subject=subject,
                message=message,
                is_public=is_public
            )
            db.session.add(new_feedback)
            db.session.commit()

            # Send email
            msg = Message(
                subject=f"New Message from {name}: {subject}",
                recipients=["dishcovery101@gmail.com"],  # Replace with your email
                body=f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}"
            )
            mail.send(msg)

            # Success message
            flash("Thank you for contacting us! We'll get back to you shortly.", "success")
            return redirect(url_for('main.contact'))

        except Exception as e:
            db.session.rollback()
            flash("An error occurred while submitting your message. Please try again.", "danger")
            print(f"Error: {e}")

    # Fetch public comments to display
    public_comments = Feedback.query.filter_by(is_public=True).order_by(Feedback.created_at.desc()).all()

    return render_template('contact.html', form=form, public_comments=public_comments)



@main.route('/toggle_favorite', methods=['POST'])
def toggle_favorite():
    if 'email' not in session:
        return jsonify({"error": "User not logged in"}), 403

    user = User.query.filter_by(email=session['email']).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.json
    recipename = data.get('recipename')
    chef_email = data.get('chef_email')

    if not recipename or not chef_email:
        return jsonify({"error": "Invalid recipe data"}), 400

    # Toggle favorite
    if user.is_favorite(recipename, chef_email):
        user.remove_from_favorites(recipename, chef_email)
        action = "removed"
    else:
        user.add_to_favorites(recipename, chef_email)
        action = "added"

    try:
        db.session.commit()
        return jsonify({"message": f"Recipe {action} in favorites", "action": action}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update favorites", "details": str(e)}), 500

@main.route('/wishlist')
def wishlist():
    if 'email' not in session or session.get('role') != 'customer':
        flash('You need to log in as a customer to view your wishlist.', 'danger')
        return redirect(url_for('main.dashboard'))

    user = User.query.filter_by(email=session['email']).first()
   
    favorite_recipes = []
    if user and user.favorites:
        for fav in user.favorites:
            recipe = Recipe.query.filter_by(recipename=fav['recipename'], chef_email=fav['chef_email']).first()
            if recipe:
                avg_rating = (
                    db.session.query(func.avg(Review.rating))
                    .filter(Review.recipename == recipe.recipename)
                    .scalar()
                )
                favorite_recipes.append({
                    "recipe": recipe,
                    "avg_rating": round(avg_rating, 1) if avg_rating else None,
                    "is_liked": True
                })

    return render_template('wishlist.html', favorite_recipes=favorite_recipes)


@main.app_template_filter('fromjson')
def fromjson(value):
    try:
        return json.loads(value) if value else []
    except (ValueError, TypeError):
        return []

@main.route('/fix_image_paths', methods=['GET'])
def fix_image_paths():
    recipes = Recipe.query.all()
    for recipe in recipes:
        if recipe.image and '\\' in recipe.image:
            # Convert Windows-style paths to relative paths
            corrected_path = recipe.image.split('static\\images\\')[-1]  # Extract the relative path
            corrected_path = corrected_path.replace("\\", "/")
            recipe.image = f'images/{corrected_path}'
    db.session.commit()
    return "Image paths fixed successfully!"


@main.route('/edit_chef_profile', methods=['GET', 'POST'])
def edit_chef_profile():
    # Controleer of de gebruiker een chef is
    user = User.query.filter_by(email=session.get('email')).first()

    if not user or not user.is_chef:
        flash('You need to log in as a chef to access this page.', 'danger')
        return redirect(url_for('main.dashboard'))

    form = ChefProfileForm(obj=user)

    # Bereken statistieken voor de preview
    recipes = Recipe.query.filter_by(chef_email=user.email).all()
    total_ratings = 0
    rating_count = 0

    for recipe in recipes:
        recipe_ratings = db.session.query(func.sum(Review.rating)).filter(Review.recipename == recipe.recipename).scalar() or 0
        recipe_count = db.session.query(func.count(Review.rating)).filter(Review.recipename == recipe.recipename).scalar()
        total_ratings += recipe_ratings
        rating_count += recipe_count

    avg_rating = round(total_ratings / rating_count, 1) if rating_count > 0 else None

    chef = User.query.filter_by(email=recipe.chef_email).first()

    total_recipes_sold = Transaction.query.filter_by(chef_email=chef.email).count()


    if form.validate_on_submit():
        try:
            # Update beschrijving
            user.chef_description = form.chef_description.data

            # Update profielfoto
            if form.profile_picture.data:
                upload_folder = os.path.join(current_app.root_path, 'static/images')
                os.makedirs(upload_folder, exist_ok=True)

                image_file = form.profile_picture.data
                filename = secure_filename(image_file.filename)
                file_path = os.path.join(upload_folder, filename)
                image_file.save(file_path)
                user.profile_picture = f'images/{filename}'

            # Opslaan in database
            db.session.commit()
            flash('Your profile has been updated successfully!', 'success')
            return redirect(url_for('main.edit_chef_profile'))

        except Exception as e:
            db.session.rollback()
            flash(f"Error updating profile: {e}", 'danger')

    return render_template(
        'edit_chef_profile.html',
        form=form,
        user=user,
        avg_rating=avg_rating,
        total_recipes_sold=total_recipes_sold
    )


@main.route('/chef_recipes/<chef_email>', methods=['GET'])
def chef_recipes(chef_email):
    # Fetch chef details
    chef = User.query.filter_by(email=chef_email).first()
    if not chef:
        flash('Chef not found.', 'danger')
        return redirect(url_for('main.dashboard'))

    # Fetch recipes by this chef
    chef_recipes = Recipe.query.filter_by(chef_email=chef_email).all()

    # Calculate average rating for this chef
    chef_avg_rating = (
        db.session.query(func.avg(Review.rating))
        .filter(Review.chef_email == chef_email)
        .scalar()
    )
    chef_avg_rating = round(chef_avg_rating, 1) if chef_avg_rating else 0

    return render_template(
        'chef_recipes.html',
        chef=chef,
        chef_recipes=chef_recipes,  # Use 'chef_recipes' to align with the template
        chef_avg_rating=chef_avg_rating  # Pass as 'chef_avg_rating' for the template
    )


from flask import Response
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io

@main.route('/download_recipe/<recipename>', methods=['GET'])
def download_recipe(recipename):
    # Fetch recipe details
    recipe = Recipe.query.filter_by(recipename=recipename).first()
    if not recipe:
        flash('Recipe not found', 'danger')
        return redirect(url_for('main.dashboard'))
    # Create PDF in memory
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Add content to the PDF
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, height - 50, f"Recipe: {recipe.recipename}")

    p.setFont("Helvetica", 12)
    p.drawString(100, height - 80, f"Chef: {recipe.chef_name}")
    p.drawString(100, height - 100, f"Cooking Time: {recipe.duration} minutes")

    # Add ingredients
    y = height - 150
    p.setFont("Helvetica-Bold", 12)
    p.drawString(100, y, "Ingredients:")
    p.setFont("Helvetica", 10)
    for ingredient in recipe.ingredients.items():
        y -= 20
        p.drawString(120, y, f"{ingredient[0]}: {ingredient[1]['quantity']} {ingredient[1]['unit']}")

    # Add preparation steps
    y -= 40
    p.setFont("Helvetica-Bold", 12)
    p.drawString(100, y, "Preparation Steps:")
    p.setFont("Helvetica", 10)
    for i, step in enumerate(recipe.preparation.split('|')):
        y -= 20
        p.drawString(120, y, f"{i+1}. {step.strip()}")

    # Finalize the PDF
    p.showPage()
    p.save()

    buffer.seek(0)
    return Response(buffer, mimetype='application/pdf',
                    headers={"Content-Disposition": f"attachment;filename={recipe.recipename}.pdf"})
