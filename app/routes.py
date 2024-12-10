import os  # Voor bestandspaden en mapbeheer
import json
from datetime import datetime  # Voor datum- en tijdstempels
from flask import Blueprint, render_template, request, session, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename  # Voor veilige bestandsnamen bij uploads
from app import db  # SQLAlchemy-instantie
from app.models import User, Recipe, Review, Transaction  # Je databasemodellen
from app.forms import RecipeForm, ReviewForm, EditProfileForm

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

    # Fetch all recipes
    recipes = Recipe.query.all()

    # Combine reviews, ratings en ingrediënten
    recipe_data = []
    for recipe in recipes:
        # Reviews en gemiddelde beoordeling
        reviews = Review.query.filter_by(recipename=recipe.recipename).all()
        avg_rating = (
            db.session.query(db.func.avg(Review.rating))
            .filter(Review.recipename == recipe.recipename)
            .scalar()
        )
        avg_rating = round(avg_rating, 1) if avg_rating else None

        # Ingrediënten verwerken
        ingredients_list = []
        if recipe.ingredients:
            try:
                ingredients = json.loads(recipe.ingredients)  # Parse JSON string
                for item in ingredients:
                    ingredients_list.append(f"{item['quantity']} {item['ingredient']}")
            except json.JSONDecodeError:
                flash(f"Error decoding ingredients for recipe {recipe.recipename}.", "warning")
        
        # Voeg alle data toe aan `recipe_data`
        recipe_data.append({
            'recipe': recipe,
            'reviews': reviews,
            'avg_rating': avg_rating,
            'ingredients_list': ingredients_list
        })

    return render_template(
        'dashboard.html',
        user=user,
        recipe_data=recipe_data,
        role=session.get('role')
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

    if form.validate_on_submit():
        try:
            # Maak de uploadmap als die niet bestaat
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

            # Haal de ingrediënten en hoeveelheden op
            ingredients = request.form.getlist('ingredients[]')
            quantities = request.form.getlist('quantities[]')

            # Maak een lijst van ingrediënten in JSON-indeling
            ingredient_list = [
                {"ingredient": ingredient.strip(), "quantity": quantity.strip()}
                for ingredient, quantity in zip(ingredients, quantities) if ingredient and quantity
            ]
            print("Processed ingredients:", ingredient_list)

            # Maak een nieuw receptobject
            new_recipe = Recipe(
                recipename=form.recipename.data,
                chef_email=session['email'],
                description=form.description.data,
                duration=form.duration.data,
                price=form.price.data,
                ingredients=json.dumps(ingredient_list),  # Converteer naar JSON-string
                allergiesrec=form.allergiesrec.data,
                image=relative_path
            )

            # Voeg toe aan de database en sla op
            db.session.add(new_recipe)
            db.session.commit()
            flash('Recipe added successfully!', 'success')
            return redirect(url_for('main.my_uploads'))

        except Exception as e:
            db.session.rollback()
            flash(f"Error saving recipe: {e}", 'danger')
            print("Error:", str(e))

    return render_template('add_recipe.html', form=form)




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
            # Parse JSON ingredients
            ingredients_list = []
            if recipe.ingredients:
                try:
                    ingredients = json.loads(recipe.ingredients)
                    for item in ingredients:
                        ingredients_list.append(f"{item['quantity']} {item['ingredient']}")
                except (json.JSONDecodeError, KeyError):
                    ingredients_list = ["Invalid ingredient format"]

            chef = User.query.filter_by(email=recipe.chef_email).first()
            purchased_recipes.append({
                "recipename": recipe.recipename,
                "chef_name": chef.name if chef else "Unknown",
                "description": recipe.description,
                "duration": recipe.duration,
                "price": recipe.price,
                "ingredients_list": ingredients_list,  # Parsed ingredients list
                "allergiesrec": recipe.allergiesrec,
                "image": recipe.image
            })

    return render_template('my_recipes.html', recipes=purchased_recipes)


@main.route('/recipe/<recipename>', methods=['GET'])
def recipe_detail(recipename):
    recipe = Recipe.query.filter_by(recipename=recipename).first()
    if not recipe:
        flash('Recipe not found.', 'danger')
        return redirect(url_for('main.dashboard'))

    user_email = session.get('email')
    user_review = Review.query.filter_by(recipename=recipename, consumer_email=user_email).first()

    # Parse JSON ingredients for detail view
    ingredients_list = []
    if recipe.ingredients:
        try:
            ingredients = json.loads(recipe.ingredients)
            for item in ingredients:
                ingredients_list.append(f"{item['quantity']} {item['ingredient']}")
        except (json.JSONDecodeError, KeyError):
            ingredients_list = ["Invalid ingredient format"]

    return render_template(
        'recipe_detail.html',
        recipe=recipe,
        user_review=user_review,
        ingredients_list=ingredients_list
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
                # Parse de JSON-string voor ingrediënten
                ingredients = json.loads(recipe.ingredients)
                for item in ingredients:
                    ingredients_list.append(f"{item['quantity']} {item['ingredient']}")
            except (json.JSONDecodeError, KeyError):
                # Voeg een standaardbericht toe als het format niet klopt
                ingredients_list = ["Invalid ingredient format"]

        # Voeg de data toe aan de lijst
        uploads_data.append({
            'recipe': recipe,
            'ingredients_list': ingredients_list
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

    # Verwerk ingrediënten uit JSON
    ingredients_list = []
    if recipe.ingredients:
        try:
            ingredients = json.loads(recipe.ingredients)  # Parse JSON string
            for item in ingredients:
                ingredients_list.append(f"{item['quantity']} {item['ingredient']}")
        except (json.JSONDecodeError, KeyError):
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
            return redirect(url_for('main.recipe_detail', recipename=recipename))
        except Exception as e:
            db.session.rollback()
            flash(f"Error submitting review: {e}", 'danger')

    return render_template('add_review.html', recipe=recipe, transaction=transaction)

@main.route('/edit_recipe/<recipename>', methods=['GET', 'POST'])
def edit_recipe(recipename):
    # Zoek het recept op
    recipe = Recipe.query.filter_by(recipename=recipename).first()
    if not recipe:
        flash('Recipe not found.', 'danger')
        return redirect(url_for('main.my_uploads'))

    # Decodeer ingrediënten uit JSON
    ingredients = []
    if recipe.ingredients:
        try:
            ingredients = json.loads(recipe.ingredients)
        except json.JSONDecodeError:
            flash('Error loading ingredients.', 'danger')

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

            # Werk ingrediënten bij
            ingredient_names = request.form.getlist('ingredients[]')
            ingredient_quantities = request.form.getlist('quantities[]')
            updated_ingredients = [
                {"ingredient": name.strip(), "quantity": quantity.strip()}
                for name, quantity in zip(ingredient_names, ingredient_quantities) if name and quantity
            ]
            recipe.ingredients = json.dumps(updated_ingredients)

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
    # Fetch the user from the database using the email stored in the session
    user = User.query.filter_by(email=session.get('email')).first()

    # Check if the user is logged in and exists
    if not user:
        return redirect(url_for('main.login'))  # Redirect if no user found or not logged in

    # Create the form, populating it with the current user data
    form = EditProfileForm(obj=user)

    # If the form is submitted and valid, update the user information
    if form.validate_on_submit():
        user.name = form.name.data
        user.date_of_birth = form.date_of_birth.data
        user.street = form.street.data
        user.housenr = form.housenr.data
        user.postalcode = form.postalcode.data
        user.city = form.city.data
        user.country = form.country.data
        user.telephonenr = form.telephonenr.data
        user.is_chef = form.is_chef.data

        # Commit the changes to the database
        db.session.commit()

        return redirect(url_for('main.dashboard'))  # Redirect to the dashboard after saving changes

    # Pass the user data to the template
    return render_template('edit_profile.html', form=form, user=user)


@main.route('/recipe_reviews/<recipename>')
def recipe_reviews(recipename):
    recipe = Recipe.query.filter_by(recipename=recipename).first()
    if not recipe:
        flash('Recipe not found.', 'danger')
        return redirect(url_for('main.dashboard'))

    reviews = Review.query.filter_by(recipename=recipename).all()
    avg_rating = (
        db.session.query(db.func.avg(Review.rating))
        .filter(Review.recipename == recipename)
        .scalar()
    )
    avg_rating = round(avg_rating, 1) if avg_rating else None

    # Parse JSON ingredients for display
    ingredients_list = []
    if recipe.ingredients:
        try:
            ingredients = json.loads(recipe.ingredients)
            for item in ingredients:
                ingredients_list.append(f"{item['quantity']} {item['ingredient']}")
        except (json.JSONDecodeError, KeyError):
            ingredients_list = ["Invalid ingredient format"]

    return render_template(
        'recipe_reviews.html',
        recipe=recipe,
        reviews=reviews,
        avg_rating=avg_rating,
        ingredients_list=ingredients_list
    )
