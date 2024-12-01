# app/routes.py

from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from app import db
from app.models import User
from app.forms import UserForm, LoginForm

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/register', methods=['GET', 'POST'])
def register():
    form = UserForm()

    #validate if form is submitted
    if form.validate_on_submit():
        print("Form is submitted")
        print(f"E-mail: {form.email.data}")
        # Save or process the data

        #does user already exist 
        if User.query.filter_by(email=form.email.data).first():
            print(f"The email {form.email.data} is already in use.")
            flash('This email is already in use, pic another one or login', 'danger')
            return redirect(url_for('main.register'))
            
        # Introduce a new user
        new_user = User(
            email=form.email.data,
            name=form.name.data,
            date_of_birth=form.date_of_birth.data,
            street = form.street.data,
            housenr=form.housenr.data,
            postalcode=form.postalcode.data,
            city=form.city.data,
            country=form.country.data,
            telephonenr=form.telephonenr.data,
        )

            # Add new user to tge database
        print("User is being added to the database...")
        db.session.add(new_user)
        db.session.commit()

        # Message of validation
        flash('You are registered succesfully', 'success')

                # Debugging: validate the redirect
        print("Redirecten naar de loginpagina...")

                # Directe redirect to loginpage
        return redirect(url_for('main.login'))
    
        # AIf the form isn't submitted or not valid, show the registrationForm

    print("Form not submitted succesfully")
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

@main.route('/logout')
def logout():
    # Verwijder de e-mail uit de sessie om de gebruiker uit te loggen
    session.pop('email', None)
    flash('You have been logged out.', 'info')
    return render_template('logout.html')
