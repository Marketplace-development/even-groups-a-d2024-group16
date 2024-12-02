# app/routes.py

from flask import Blueprint, render_template, request, session, redirect, url_for, flash
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
    print("Login route is reached")  # Dit moet in je terminal verschijnen
    form = LoginForm()
    
    if form.validate_on_submit():
        email = form.email.data
        user = User.query.filter_by(email=email).first()
        
        if user:
            session['email'] = user.email  # Save the email in the Session
            flash(f'Logged in with email {user.email}', 'success')
            return redirect(url_for('main.dashboard'))  # Redirect to the dashboard
        else:
            flash('Email not found', 'danger')
    
    return render_template('login.html', form=form)

@main.route('/dashboard')
def dashboard():
    if 'email' not in session:
        flash('You have to login first', 'danger')
        return redirect(url_for('main.login'))
    
    user = User.query.get(session['email'])  # Get user with email
    
    return render_template('dashboard.html', user=user)

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
    if 'email' not in session:
        flash('You need to be logged in to add a recipe.', 'danger')
        return redirect(url_for('main.login'))

    form = RecipeForm()
    if form.validate_on_submit():
        # Controleer of het recept al bestaat
        existing_recipe = Recipe.query.filter_by(recipename=form.recipename.data).first()
        if existing_recipe:
            flash('A recipe with this name already exists. Please choose a different name.', 'danger')
            return redirect(url_for('main.add_recipe'))

        # Zoek de ingelogde gebruiker
        user = User.query.filter_by(email=session['email']).first()
        
        # Maak een nieuw recept aan
        new_recipe = Recipe(
            recipename=form.recipename.data,
            chef_email=user.email,
            description=form.description.data,
            duration=form.duration.data,
            price=form.price.data,
            ingredients=form.ingredients.data,
            allergiesrec=form.allergiesrec.data,
            image=form.image.data
        )
        
        # Voeg het nieuwe recept toe aan de database
        db.session.add(new_recipe)
        db.session.commit()

        flash('Recipe has been added successfully!', 'success')
        return redirect(url_for('main.list_recipes'))

    return render_template('add_recipe.html', form=form)



@main.route('/recipe/<recipename>')
def recipe_detail(recipename):
    recipe = Recipe.query.filter_by(recipename=recipename).first()
    if recipe is None:
        flash('Recipe not found', 'danger')
        return redirect(url_for('main.list_recipes'))
    return render_template('recipe_detail.html', recipe=recipe)
