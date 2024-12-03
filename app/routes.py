# app/routes.py
import os  # Voor bestandspaden en mapbeheer
from datetime import datetime  # Voor datum- en tijdstempels

# Flask-specifieke imports
from flask import Blueprint, render_template, request, session, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename  # Voor veilige bestandsnamen bij uploads

# Database en modellen
from app import db  # SQLAlchemy-instantie
from app.models import User, Recipe, Transaction  # Je databasemodellen

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

        # Voeg recept toe aan de database
        new_recipe = Recipe(
            recipename=form.recipename.data,
            chef_email=session['email'],
            description=form.description.data,
            duration=form.duration.data,
            price=form.price.data,
            ingredients=form.ingredients.data,
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
    # Fetch the recipe from the database
    recipe = Recipe.query.filter_by(recipename=recipename).first()

    if recipe is None:
        flash('Recipe not found', 'danger')
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        # Simulate the buying process (e.g., create a transaction)
        if 'email' not in session:
            flash('You need to be logged in to buy a recipe.', 'danger')
            return redirect(url_for('main.login'))

        # Create a transaction (example logic)
        user_email = session['email']
        chef_email = recipe.chef_email
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
        return redirect(url_for('main.dashboard'))

    # Render the buy_recipe page
    return render_template('buy_recipe.html', recipe=recipe)

