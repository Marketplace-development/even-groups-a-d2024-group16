import os  # Voor bestandspaden en mapbeheer
import json
from datetime import datetime  # Voor datum- en tijdstempels
from flask import Blueprint, render_template, request, session, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename  # Voor veilige bestandsnamen bij uploads
from app import db  # SQLAlchemy-instantie
from app.models import User, Recipe, Review, Transaction  # Je databasemodellen
from app.forms import RecipeForm, ReviewForm, EditProfileForm
from app.ingredients import ingredienten
from app.dropdowns import get_allergens, get_categories, get_origins
from sqlalchemy import and_, or_
from app.filters import apply_filters
# Formulieren
from app.forms import UserForm, LoginForm, RecipeForm  # Je Flask-WTF-formulieren

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/register', methods=['GET', 'POST'])
def register():
    form = UserForm()

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

        # Maak nieuwe gebruiker aan
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
            is_chef=is_chef  # Gebruik de juiste waarde van is_chef
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


    # If the form isn't submitted or is not valid, show the registration form
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

    user = User.query.filter_by(email=session['email']).first()
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('main.login'))

    # Haal gegevens op voor dropdowns
    categories = get_categories()
    origins = get_origins()
    allergens = get_allergens()

    # Filters ophalen
    filters = {
        'ingredients': request.args.getlist('ingredients'),
        'min_rating': request.args.get('min_rating'),
        'duration': request.args.get('duration'),
        'price': request.args.get('price'),
        'category': request.args.get('category'),
        'origin': request.args.get('origin'),
        'allergies': request.args.getlist('allergies')
    }

    # Query starten
    query = Recipe.query

    # Filters toepassen, behalve min_rating
    query = apply_filters(query, filters)

    # Gefilterde recepten ophalen
    recipes = query.all()

    # Verwerk recepten en voeg avg_rating toe
    recipe_data = []
    for recipe in recipes:
        # Bereken gemiddelde beoordeling
        avg_rating = (
            db.session.query(db.func.avg(Review.rating))
            .filter(Review.recipename == recipe.recipename)
            .scalar()
        )
        avg_rating = round(avg_rating, 1) if avg_rating else None

        # Ingrediënten verwerken
        ingredients_list = []
        if recipe.ingredients:
            for ingredient, details in recipe.ingredients.items():
                ingredients_list.append({
                    'quantity': details['quantity'],
                    'unit': details.get('unit', ''),
                    'ingredient': ingredient
                })

        recipe_data.append({
            'recipe': recipe,
            'avg_rating': avg_rating,
            'ingredients_list': ingredients_list
        })

    # Filter op min_rating na het berekenen van avg_rating
    if filters.get('min_rating'):
        min_rating = float(filters['min_rating'])
        recipe_data = [r for r in recipe_data if r['avg_rating'] and r['avg_rating'] >= min_rating]

    return render_template(
        'dashboard.html',
        user=user,
        recipe_data=recipe_data,
        categories=categories,
        origins=origins,
        allergens=allergens,
        ingredienten=ingredienten
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

    # Haal allergenen op uit de database of een statische lijst
    allergens = get_allergens()

    if form.validate_on_submit():
        try:
            # Zorg ervoor dat de uploadmap bestaat
            upload_folder = os.path.join(current_app.root_path, 'static/images')
            os.makedirs(upload_folder, exist_ok=True)

            # Verwerk de afbeelding
            image_file = form.image.data
            filename = secure_filename(image_file.filename) if image_file else None
            relative_path = None
            if filename:
                file_path = os.path.join(upload_folder, filename)
                image_file.save(file_path)
                relative_path = f'images/{filename}'

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
        ingredienten=ingredienten,
        allergens=allergens  # Geef allergenen door aan de template
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

    chef_email = session['email']
    uploads = Recipe.query.filter_by(chef_email=chef_email).all()  # Filter recepten van de chef

    # Verwerk de recepten en parse de ingrediënten
    uploads_data = []
    for recipe in uploads:
        ingredients_list = []
        if recipe.ingredients:
            try:
                # De ingrediënten zijn al een dictionary, dus we hoeven ze niet te parsen
                for ingredient, details in recipe.ingredients.items():
                    # Voeg de hoeveelheid, maateenheid en ingrediënt toe aan de lijst
                    quantity = details.get("quantity", "")
                    unit = details.get("unit", "")
                    ingredients_list.append(f"{quantity} {unit} of {ingredient}")
            except KeyError:
                # Voeg een standaardbericht toe als het format niet klopt
                ingredients_list = ["Invalid ingredient format"]

        # Bereken de gemiddelde beoordeling voor het recept
        avg_rating = (
            db.session.query(db.func.avg(Review.rating))
            .filter(Review.recipename == recipe.recipename)
            .scalar()
        )
        avg_rating = round(avg_rating, 1) if avg_rating else None

        # Voeg de gegevens toe aan de lijst
        uploads_data.append({
            'recipe': recipe,
            'ingredients_list': ingredients_list,
            'avg_rating': avg_rating
        })

    return render_template('my_uploads.html', uploads_data=uploads_data)  # uploads_data doorgeven aan sjabloon




@main.route('/buy_recipe/<recipename>', methods=['GET', 'POST'])
def buy_recipe(recipename):
    # Haal het recept op uit de database
    recipe = Recipe.query.filter_by(recipename=recipename).first()

    if recipe is None:
        flash('Recipe not found', 'danger')
        return redirect(url_for('main.dashboard'))

    # Check of de gebruiker is ingelogd
    if 'email' not in session:
        flash('You need to be logged in to buy a recipe.', 'danger')
        return redirect(url_for('main.login'))

    # Verwerk ingrediënten (nu uit de opgeslagen dictionary, niet meer JSON)
    ingredients_list = []
    if recipe.ingredients:
        try:
            # Loop door de ingrediënten dictionary
            for ingredient, details in recipe.ingredients.items():
                # Voeg zowel de hoeveelheid, maateenheid als ingrediënt toe aan de lijst
                ingredients_list.append({
                    'quantity': details['quantity'],
                    'unit': details.get('unit', ''),  # Voeg een lege string toe als er geen unit is
                    'ingredient': ingredient
                })
        except KeyError:
            ingredients_list = ["Invalid ingredient format"]

    # Verwerk aankoop bij POST-verzoek
    if request.method == 'POST':
        user_email = session['email']
        chef_email = recipe.chef_email

        # Controleer of de gebruiker dit recept al gekocht heeft
        existing_transaction = Transaction.query.filter_by(
            consumer_email=user_email,
            recipename=recipename
        ).first()

        if existing_transaction:
            flash('You have already purchased this recipe.', 'warning')
            return redirect(url_for('main.dashboard'))

        # Maak de transactie aan
        transaction = Transaction(
            transactiondate=datetime.now(),
            price=recipe.price,
            consumer_email=user_email,
            chef_email=chef_email,
            recipename=recipename
        )
        db.session.add(transaction)
        db.session.commit()

        flash('Recipe purchased successfully!', 'success')
        return redirect(url_for('main.my_recipes'))

    # Render de buy_recipe pagina bij GET-verzoek
    return render_template(
        'buy_recipe.html',
        recipe=recipe,
        ingredients_list=ingredients_list
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
    # Zoek het recept op in de database
    recipe = Recipe.query.filter_by(recipename=recipename).first()
    
    if not recipe:
        flash('Recipe not found.', 'danger')
        return redirect(url_for('main.my_uploads'))

    # Ingrediënten ophalen uit de database (ze zijn een dictionary)
    ingredients = recipe.ingredients if recipe.ingredients else {}

    # Maak formulier met bestaande gegevens
    form = RecipeForm(obj=recipe)

    if form.validate_on_submit():
        try:
            # Werk receptgegevens bij
            recipe.recipename = form.recipename.data
            recipe.description = form.description.data
            recipe.duration = form.duration.data
            recipe.price = form.price.data
            recipe.allergiesrec = form.allergiesrec.data
            recipe.origin = form.origin.data
            recipe.category = form.category.data
            
            # Preparation steps ophalen en combineren met een pipe
            preparation_steps = request.form.getlist('preparation_steps[]')
            recipe.preparation = '|'.join([step.strip() for step in preparation_steps if step.strip()])

            # Werk ingrediënten bij
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

            # Werk de ingrediënten bij in de database
            recipe.ingredients = updated_ingredients

            # Werk afbeelding bij indien gewijzigd
            if form.image.data:
                upload_folder = os.path.join(current_app.root_path, 'static/images')
                os.makedirs(upload_folder, exist_ok=True)

                image_file = form.image.data
                filename = secure_filename(image_file.filename)
                file_path = os.path.join(upload_folder, filename)
                image_file.save(file_path)
                recipe.image = f'images/{filename}'

            # Sla wijzigingen op
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
        ingredients=ingredients
    )




@main.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    # Haal de gebruiker op uit de database op basis van het e-mailadres uit de sessie
    user = User.query.filter_by(email=session.get('email')).first()

    # Controleer of de gebruiker ingelogd is en bestaat
    if not user:
        return redirect(url_for('main.login'))  # Redirect als de gebruiker niet gevonden is of niet ingelogd is

    # Maak het formulier, vul het in met de huidige gebruikersdata
    form = EditProfileForm(obj=user)

    # Als het formulier wordt ingediend en geldig is, werk dan de gebruikersinformatie bij
    if form.validate_on_submit():
        user.name = form.name.data
        user.date_of_birth = form.date_of_birth.data
        user.street = form.street.data
        user.housenr = form.housenr.data
        user.postalcode = form.postalcode.data
        user.city = form.city.data
        user.country = form.country.data
        user.telephonenr = form.telephonenr.data
        
        # Bewaar de waarde van is_chef ongewijzigd (zorg ervoor dat het niet wordt overschreven)
        # Alleen als de gebruiker een chef is, behouden we de waarde van is_chef
        if user.is_chef:  # Alleen als de gebruiker een chef is
            user.is_chef = user.is_chef

        # Commit de wijzigingen naar de database
        db.session.commit()

        # Redirect naar het dashboard nadat de wijzigingen zijn opgeslagen
        return redirect(url_for('main.dashboard'))  # Redirect naar het dashboard na het opslaan van wijzigingen

    # Geef de gebruikersgegevens door naar de template
    return render_template('edit_profile.html', form=form, user=user)


@main.route('/recipe_reviews/<recipename>')
def recipe_reviews(recipename):
    # Haal het recept op uit de database
    recipe = Recipe.query.filter_by(recipename=recipename).first()
    if not recipe:
        flash('Recipe not found.', 'danger')
        return redirect(url_for('main.dashboard'))

    # Haal de beoordelingen voor het recept op
    reviews = Review.query.filter_by(recipename=recipename).all()

    # Bereken de gemiddelde rating
    avg_rating = (
        db.session.query(db.func.avg(Review.rating))
        .filter(Review.recipename == recipename)
        .scalar()
    )
    avg_rating = round(avg_rating, 1) if avg_rating else None

    # Verwerk de ingrediënten voor weergave (nu direct als dictionary)
    ingredients_list = []
    if recipe.ingredients:
        try:
            # Loop door de ingrediënten dictionary (geen JSON decoding nodig)
            for ingredient, details in recipe.ingredients.items():
                # Voeg de quantity, unit en ingredient toe aan de lijst
                ingredients_list.append({
                    'quantity': details['quantity'],
                    'unit': details.get('unit', ''),  # Voeg unit toe, als die bestaat
                    'ingredient': ingredient
                })
        except KeyError:
            ingredients_list = ["Invalid ingredient format"]

    # Render de recipe_reviews pagina
    return render_template(
        'recipe_reviews.html',
        recipe=recipe,
        reviews=reviews,
        avg_rating=avg_rating,
        ingredients_list=ingredients_list
    )
