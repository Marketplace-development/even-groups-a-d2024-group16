import os  # Voor bestandspaden en mapbeheer
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

    # Fetch reviews and average ratings for each recipe
    recipe_data = []
    for recipe in recipes:
        reviews = Review.query.filter_by(recipename=recipe.recipename).all()
        avg_rating = (
            db.session.query(db.func.avg(Review.rating))
            .filter(Review.recipename == recipe.recipename)
            .scalar()
        )
        avg_rating = round(avg_rating, 1) if avg_rating else None

        recipe_data.append({
            'recipe': recipe,
            'reviews': reviews,
            'avg_rating': avg_rating
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
        # Map voor afbeeldingen
        upload_folder = os.path.join(current_app.root_path, 'static/images')
        
        # Controleer of de map bestaat
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        # Sla de afbeelding veilig op
        image_file = form.image.data
        filename = secure_filename(image_file.filename)
        file_path = os.path.join(upload_folder, filename)
        image_file.save(file_path)

        # Sla alleen het relatieve pad op in de database
        relative_path = f'images/{filename}'

        ingredients = form.ingredients.data

        # Voeg recept toe aan de database
        new_recipe = Recipe(
            recipename=form.recipename.data,
            chef_email=session['email'],
            description=form.description.data,
            duration=form.duration.data,
            price=form.price.data,
            ingredients=ingredients,
            allergiesrec=form.allergiesrec.data,
            image=relative_path  # Alleen het bestandspad opslaan
        )
        db.session.add(new_recipe)
        db.session.commit()
        flash('Recipe added successfully!', 'success')
        return redirect(url_for('main.my_uploads'))

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
            chef = User.query.filter_by(email=recipe.chef_email).first()
            purchased_recipes.append({
                "recipename": recipe.recipename,
                "chef_name": chef.name if chef else "Unknown",
                "description": recipe.description,
                "duration": recipe.duration,
                "price": recipe.price,
                "ingredients": recipe.ingredients,
                "allergiesrec": recipe.allergiesrec,
                "image": recipe.image
            })

    return render_template('my_recipes.html', recipes=purchased_recipes)



@main.route('/recipe/<recipename>', methods=['GET'])
def recipe_detail(recipename):
    # Zoek het recept op basis van recipename
    recipe = Recipe.query.filter_by(recipename=recipename).first()

    if recipe is None:
        flash('Recipe not found', 'danger')
        return redirect(url_for('main.list_recipes'))

    # Render de template voor de receptdetails
    return render_template('recipe_detail.html', recipe=recipe)


@main.route('/my_uploads')
def my_uploads():
    if 'email' not in session or session.get('role') != 'chef':
        flash('You need to log in as a chef to access this page.', 'danger')
        return redirect(url_for('main.login'))

    chef_email = session['email']
    uploads = Recipe.query.filter_by(chef_email=chef_email).all()  # Filter recepten van de chef
    return render_template('my_uploads.html', recipes=uploads)


@main.route('/my_library')
def my_library():
    if 'email' not in session or session.get('role') != 'chef':
        flash('You need to log in as a chef to access this page.', 'danger')
        return redirect(url_for('main.login'))

    chef_email = session['email']
    library_recipes = Recipe.query.filter_by(chef_email=chef_email).all()  # Filter recepten van de chef
    return render_template('my_library.html', recipes=library_recipes)



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

    # Als het een POST-verzoek is (bij klikken op "Confirm Purchase")
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
    return render_template('buy_recipe.html', recipe=recipe)

@main.route('/add_review/<recipename>', methods=['GET', 'POST'])
def add_review(recipename):
    # Ensure user is logged in
    if 'email' not in session:
        flash('You need to log in to add a review.', 'danger')
        return redirect(url_for('main.login'))

    # Get the recipe
    recipe = Recipe.query.filter_by(recipename=recipename).first()
    if not recipe:
        flash('Recipe not found.', 'danger')
        return redirect(url_for('main.my_recipes'))

    # Fetch the transaction linked to the recipe
    transaction = Transaction.query.filter_by(
        recipename=recipename,
        consumer_email=session['email']
    ).first()

    if not transaction:
        flash('No transaction found for this recipe.', 'danger')
        return redirect(url_for('main.my_recipes'))

    if request.method == 'POST':
        # Retrieve data from the form
        rating = request.form.get('rating')
        comment = request.form.get('comment')

        # Validate inputs
        if not rating or not comment:
            flash('All fields are required.', 'danger')
            return redirect(url_for('main.add_review', recipename=recipename))

        # Save the review to the database
        new_review = Review(
            comment=comment,
            rating=int(rating),
            consumer_email=session['email'],
            recipename=recipename,
            transactionid=transaction.transactionid  # Associate with the transaction
        )
        db.session.add(new_review)
        db.session.commit()

        flash('Review submitted successfully!', 'success')
        return redirect(url_for('main.recipe_detail', recipename=recipename))

    return render_template('add_review.html', recipe=recipe, transaction=transaction)


@main.route('/edit_recipe/<recipename>', methods=['GET', 'POST'])
def edit_recipe(recipename):
    recipe = Recipe.query.filter_by(recipename=recipename).first()
    if recipe is None:
        flash('Recipe not found', 'danger')
        return redirect(url_for('main.my_uploads'))

    form = RecipeForm()

    # Vul het formulier met de huidige gegevens van het recept bij een GET-verzoek
    if request.method == 'GET':
        form.recipename.data = recipe.recipename
        form.description.data = recipe.description
        form.ingredients.data = recipe.ingredients
        form.price.data = recipe.price
        form.allergiesrec.data = recipe.allergiesrec
        form.duration.data = recipe.duration  # Zorg ervoor dat je duration ook vult

    # Verwerk het formulier bij een POST-verzoek
    if form.validate_on_submit():
        # Werk de receptgegevens bij
        recipe.recipename = form.recipename.data
        recipe.description = form.description.data
        recipe.ingredients = form.ingredients.data
        recipe.price = form.price.data
        recipe.allergiesrec = form.allergiesrec.data
        recipe.duration = form.duration.data  # Update de cooking time (duur)

        # Als er een nieuwe afbeelding is geüpload, werk het bestand bij
        if form.image.data:
            upload_folder = os.path.join(current_app.root_path, 'static/images')
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)

            image_file = form.image.data
            filename = secure_filename(image_file.filename)
            file_path = os.path.join(upload_folder, filename)
            image_file.save(file_path)

            # Update het bestandspad naar de afbeelding in de database
            relative_path = f'images/{filename}'
            recipe.image = relative_path

        try:
            db.session.commit()  # Pas de wijzigingen toe op de database
            flash('Recipe updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()  # Rollback in geval van een fout
            flash(f'Error updating recipe: {str(e)}', 'danger')

        return redirect(url_for('main.my_uploads'))

    return render_template('edit_recipe.html', form=form, recipe=recipe)


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

    return render_template('recipe_reviews.html', recipe=recipe, reviews=reviews, avg_rating=avg_rating)
