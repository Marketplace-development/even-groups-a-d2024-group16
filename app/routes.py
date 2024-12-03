# app/routes.py
import os
from flask import Blueprint, render_template, request, session, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
from app import db
from app.models import User, Recipe
from app.forms import UserForm, LoginForm, RecipeForm

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

    recipes = Recipe.query.all()
    return render_template(
        'dashboard.html',
        user=user,
        recipes=recipes,
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

import os
from flask import current_app, flash, redirect, render_template, url_for
from werkzeug.utils import secure_filename
from app.models import Recipe
from app.forms import RecipeForm
from app import db

@main.route('/add_recipe', methods=['GET', 'POST'])
def add_recipe():
    # Controleer of de gebruiker is ingelogd als chef
    if 'email' not in session or session.get('role') != 'chef':
        flash('You need to log in as a chef to add recipes.', 'danger')
        return redirect(url_for('main.login'))

    form = RecipeForm()

    # Als het een GET-verzoek is, render het formulier om een nieuw recept toe te voegen
    if request.method == 'GET':
        return render_template('add_recipe.html', form=form)  # Zorg ervoor dat er een template wordt geretourneerd

    # Als het een POST-verzoek is en het formulier is correct ingevuld
    if form.validate_on_submit():
        # Bepaal de map voor afbeeldingen
        upload_folder = os.path.join(current_app.root_path, 'static/images')
        
        # Controleer of de map bestaat en maak deze aan indien nodig
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        # Sla de afbeelding veilig op
        image_file = secure_filename(form.image.data.filename)
        image_path = os.path.join(upload_folder, image_file)
        form.image.data.save(image_path)

        # Haal het e-mailadres van de ingelogde chef op uit de sessie
        chef_email = session['email']

        # Voeg het recept toe aan de database, inclusief het e-mailadres van de chef
        new_recipe = Recipe(
            recipename=form.recipename.data,
            chef_email=chef_email,  # Chef's e-mailadres opslaan
            description=form.description.data,
            duration=form.duration.data,
            price=form.price.data,
            ingredients=form.ingredients.data,
            allergiesrec=form.allergiesrec.data,
            image=f'images/{image_file}'  # Bewaar het relatieve pad van de afbeelding
        )

        # Voeg het nieuwe recept toe aan de sessie en commit
        db.session.add(new_recipe)
        db.session.commit()

        flash('Recipe added successfully!', 'success')
        return redirect(url_for('main.dashboard'))

    # Als het formulier niet valideert of het een GET-verzoek is, render het formulier opnieuw
    return render_template('add_recipe.html', form=form)



@main.route('/my_recipes')
def my_recipes():
    if 'email' not in session or session.get('role') != 'customer':
        flash('You need to log in as a customer to access this page.', 'danger')
        return redirect(url_for('main.login'))

    recipes = []  # Voorlopig geen recepten beschikbaar
    return render_template('my_recipes.html', recipes=recipes)



@main.route('/recipe/<recipename>')
def recipe_detail(recipename):
    recipe = Recipe.query.filter_by(recipename=recipename).first()
    if recipe is None:
        flash('Recipe not found', 'danger')
        return redirect(url_for('main.list_recipes'))
    return render_template('recipe_detail.html', recipe=recipe)


@main.route('/my_uploads')
def my_uploads():
    # Controleer of de gebruiker ingelogd is en een chef is
    if 'email' not in session or session.get('role') != 'chef':
        flash('You need to log in as a chef to view your uploads.', 'danger')
        return redirect(url_for('main.login'))

    # Haal het e-mailadres van de ingelogde chef op uit de sessie
    chef_email = session['email']

    # Haal alle recepten op die zijn geüpload door de chef
    recipes = Recipe.query.filter_by(chef_email=chef_email).all()

    # Render de my_uploads template met de recepten van de chef
    return render_template('my_uploads.html', recipes=recipes)



@main.route('/my_library')
def my_library():
    if 'email' not in session or session.get('role') != 'chef':
        flash('You need to log in as a chef to access this page.', 'danger')
        return redirect(url_for('main.login'))

    chef_email = session['email']
    library_recipes = Recipe.query.filter_by(chef_email=chef_email).all()  # Filter recepten van de chef
    return render_template('my_library.html', recipes=library_recipes)
