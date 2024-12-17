import os  # For file paths and directory management
from datetime import datetime  # For date and time stamps

from flask import Blueprint, render_template, request, session, redirect, url_for, flash, current_app, jsonify
from werkzeug.utils import secure_filename  # For secure filenames when uploading
from app import db, mail  # SQLAlchemy and mail instances
from app.models import User, Recipe, Review, Transaction, Feedback  # Your database models
from app.forms import UserForm, LoginForm, RecipeForm, ReviewForm, EditProfileForm, ContactForm
from app.dropdowns import get_allergens, get_categories, get_origins
from sqlalchemy import and_, or_, func
from app.filters import apply_filters
from app.sort import apply_sorting
from app.zoekbalk import apply_search
from flask_mail import Message
from app.check_and_notify_chef import check_and_notify_chef
from .responses import get_response

main = Blueprint('main', __name__)
chatbot = Blueprint('chatbot', __name__)


@main.route('/')
def index():
    return render_template('index.html')


@main.route('/register', methods=['GET', 'POST'])
def register():
    form = UserForm()
    
    # Use allergens directly from ingredients.py
    form.allergies.choices = [(allergy, allergy) for allergy in get_allergens()]
    form.favorite_origins.choices = [(origin, origin) for origin in get_origins()]
    
    if form.validate_on_submit():
        print("Form is submitted")
        print(f"Email: {form.email.data}")

        # Retrieve the value of is_chef directly from the POST data
        is_chef_value = request.form.get('is_chef')
        print(f"Received is_chef value: {is_chef_value}")
        is_chef = True if is_chef_value == 'true' else False

        # Check if the user already exists
        if User.query.filter_by(email=form.email.data).first():
            print(f"The email {form.email.data} is already in use.")
            flash('This email is already in use, choose another one or log in', 'danger')
            return redirect(url_for('main.register'))
        
        favorite_ingredients = form.favorite_ingredients.data.split(',') if form.favorite_ingredients.data else []

        # Create a new user
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
            preferences=preferences
        )

        # Add new user to the database
        print("User is being added to the database...")
        db.session.add(new_user)
        db.session.commit()

        flash('You are registered successfully', 'success')
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

    categories = get_categories()
    origins = get_origins()
    allergens = get_allergens()

    search_query = request.args.get('search', '')

    allergies_input = request.args.get('allergies', "")
    allergies_list = [a.lower().strip() for a in allergies_input.split(",") if a]
    filters = {
        'ingredient': request.args.getlist('ingredient[]'),
        'quantity': request.args.getlist('quantity[]'),
        'unit': request.args.getlist('unit[]'),
        'allergies': allergies_list,
        'min_rating': request.args.get('min_rating'),
        'duration': request.args.get('duration'),
        'price': request.args.get('price'),
        'category': request.args.get('category'),
        'origin': request.args.get('origin'),
    }

    sort_by = request.args.get('sort_by', 'recommended' if not user.is_chef else 'price_quality')

    query = Recipe.query
    query = apply_filters(query, filters)
    query = apply_search(query, search_query)
    preferences = user.preferences or {'favorite_ingredients': [], 'favorite_origins': []}
    query = apply_sorting(query, sort_by, preferences=preferences)

    recipes = query.all()

    recipe_data = []
    user_favorites = user.favorites or []

    for recipe in recipes:
        avg_rating = (
            db.session.query(func.avg(Review.rating))
            .filter(Review.recipename == recipe.recipename)
            .scalar()
        )
        avg_rating = round(avg_rating, 1) if avg_rating else None

        ingredients_list = []
        if recipe.ingredients:
            for ingredient, details in recipe.ingredients.items():
                ingredients_list.append({
                    'quantity': details.get('quantity', ''),
                    'unit': details.get('unit', ''),
                    'ingredient': ingredient
                })

        allergies = recipe.allergiesrec.split(", ") if recipe.allergiesrec else []
        is_liked = user.is_favorite(recipe.recipename, recipe.chef_email)

        recipe_data.append({
            'recipe': recipe,
            'avg_rating': avg_rating,
            'ingredients_list': ingredients_list,
            'allergies': allergies,
            'is_liked': is_liked
        })

    if filters['allergies']:
        allergy_filters = filters['allergies']
        recipe_data = [
            r for r in recipe_data
            if not any(
                allergy in [a.lower() for a in r['allergies']]
                for allergy in allergy_filters
            )
        ]

    if filters.get('min_rating'):
        try:
            min_rating = float(filters['min_rating'])
            recipe_data = [r for r in recipe_data if r['avg_rating'] and r['avg_rating'] >= min_rating]
        except ValueError:
            flash("Invalid minimum rating value.", "danger")

    if filters.get('duration'):
        try:
            max_duration = int(filters['duration'])
            recipe_data = [r for r in recipe_data if r['recipe'].duration and r['recipe'].duration <= max_duration]
        except ValueError:
            flash("Invalid duration value.", "danger")

    if filters.get('price'):
        try:
            max_price = float(filters['price'])
            recipe_data = [r for r in recipe_data if r['recipe'].price and r['recipe'].price <= max_price]
        except ValueError:
            flash("Invalid price value.", "danger")

    if filters.get('category'):
        recipe_data = [r for r in recipe_data if r['recipe'].category == filters['category']]

    if filters.get('origin'):
        recipe_data = [r for r in recipe_data if r['recipe'].origin == filters['origin']]

    return render_template(
        'dashboard.html',
        user=user,
        recipe_data=recipe_data,
        categories=categories,
        origins=origins,
        allergens=allergens,
        sort_by=sort_by,
        user_favorites=user_favorites
    )


@main.route('/logout', methods=['GET'])
def logout():
    print("Logout route reached")
    if 'email' in session:
        session.pop('email', None)
        flash('You have been logged out successfully.', 'info')
        print("User session cleared, redirecting to index")
    return redirect(url_for('main.index'))


@main.route('/recipes', methods=['GET'])
def list_recipes():
    recipes = Recipe.query.all()
    return render_template('listing.html', recipes=recipes)


@main.route('/add_recipe', methods=['GET', 'POST'])
def add_recipe():
    if 'email' not in session or session.get('role') != 'chef':
        flash('You need to log in as a chef to add recipes.', 'danger')
        return redirect(url_for('main.login'))

    form = RecipeForm()

    allergens = get_allergens()
    categories = get_categories()
    origins = get_origins()

    if form.validate_on_submit():
        try:
            upload_folder = os.path.join(current_app.root_path, 'static/images')
            os.makedirs(upload_folder, exist_ok=True)

            image_file = form.image.data
            filename = secure_filename(image_file.filename) if image_file else None
            relative_path = None
            if filename:
                file_path = os.path.join(upload_folder, filename)
                image_file.save(file_path)
                relative_path = f'images/{filename}'

            ingredients = request.form.getlist('ingredients[]')
            quantities = request.form.getlist('quantities[]')
            units = request.form.getlist('units[]')

            ingredient_dict = {}
            for ingredient, quantity, unit in zip(ingredients, quantities, units):
                if ingredient and quantity and unit:
                    ingredient_dict[ingredient.strip()] = {
                        "quantity": quantity.strip(),
                        "unit": unit.strip()
                    }

            selected_allergens = request.form.getlist('allergiesrec[]')
            allergens_string = ', '.join(selected_allergens)

            preparation_steps = request.form.getlist('preparation_steps[]')
            preparation_instructions = '|'.join([step.strip() for step in preparation_steps if step.strip()])

            chef = User.query.filter_by(email=session['email']).first()
            chef_name = chef.name if chef else None

            new_recipe = Recipe(
                recipename=form.recipename.data,
                chef_email=session['email'],
                chef_name=chef_name,
                description=form.description.data,
                duration=form.duration.data,
                price=form.price.data,
                ingredients=ingredient_dict,
                allergiesrec=allergens_string,
                image=relative_path,
                origin=form.origin.data,
                category=form.category.data,
                preparation=preparation_instructions
            )

            db.session.add(new_recipe)
            db.session.commit()
            flash('Recipe added successfully!', 'success')
            return redirect(url_for('main.my_uploads'))

        except Exception as e:
            db.session.rollback()
            flash(f"Error saving recipe: {e}", 'danger')
            print("Error:", str(e))

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

    user_email = session['email']
    transactions = Transaction.query.filter_by(consumer_email=user_email).all()

    purchased_recipes = []
    for transaction in transactions:
        recipe = Recipe.query.filter_by(recipename=transaction.recipename, chef_email=transaction.chef_email).first()
        if recipe:
            ingredients_list = []
            if recipe.ingredients:
                try:
                    for ingredient, details in recipe.ingredients.items():
                        quantity = details['quantity']
                        unit = details.get('unit', '')
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
                "ingredients_list": ingredients_list,
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

    ingredients_list = []
    if recipe.ingredients:
        try:
            for ingredient, details in recipe.ingredients.items():
                quantity = details['quantity']
                unit = details.get('unit', '')
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
        ingredients_list=ingredients_list
    )


@main.route('/my_uploads')
def my_uploads():
    if 'email' not in session or session.get('role') != 'chef':
        flash('You need to log in as a chef to access this page.', 'danger')
        return redirect(url_for('main.login'))

    chef_email = session['email']
    uploads = Recipe.query.filter_by(chef_email=chef_email).all()

    uploads_data = []
    total_revenue = 0
    revenue_data = []
    for recipe in uploads:
        ingredients_list = []
        if recipe.ingredients:
            try:
                for ingredient, details in recipe.ingredients.items():
                    quantity = details.get("quantity", "")
                    unit = details.get("unit", "")
                    ingredients_list.append(f"{quantity} {unit} of {ingredient}")
            except KeyError:
                ingredients_list = ["Invalid ingredient format"]

        avg_rating = (
            db.session.query(func.avg(Review.rating))
            .filter(Review.recipename == recipe.recipename)
            .scalar()
        )
        avg_rating = round(avg_rating, 1) if avg_rating else None

        total_recipe_revenue = (
            db.session.query(func.sum(Transaction.price))
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
            'allergies': recipe.allergiesrec
        })

    revenue_data = sorted(revenue_data, key=lambda x: x['total_revenue'], reverse=True)[:5]

    overall_avg_rating = (
        db.session.query(func.avg(Review.rating))
        .filter(Review.chef_email == chef_email)
        .scalar()
    )
    overall_avg_rating = round(overall_avg_rating, 1) if overall_avg_rating else 0

    return render_template('my_uploads.html',
                           uploads_data=uploads_data,
                           overall_avg_rating=overall_avg_rating,
                           total_revenue=total_revenue,
                           revenue_data=revenue_data)


@main.route('/buy_recipe/<recipename>', methods=['GET', 'POST'])
def buy_recipe(recipename):
    recipe = Recipe.query.filter_by(recipename=recipename).first()

    if recipe is None:
        flash('Recipe not found', 'danger')
        return redirect(url_for('main.dashboard'))

    ingredients_to_match = [{'ingredient': ing} for ing in recipe.ingredients.keys()]

    related_recipes = Recipe.query.filter(
        (Recipe.origin == recipe.origin) | 
        (Recipe.ingredients.contains(ingredients_to_match))
    ).filter(Recipe.recipename != recipename).limit(4).all()

    if 'email' not in session:
        flash('You need to be logged in to buy a recipe.', 'danger')
        return redirect(url_for('main.login'))

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

    reviews = Review.query.filter_by(recipename=recipename, chef_email=recipe.chef_email).all()

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

        transaction = Transaction(
            transactiondate=datetime.now(),
            price=recipe.price,
            consumer_email=user_email,
            chef_email=chef_email,
            recipename=recipename
        )
        db.session.add(transaction)
        db.session.commit()

        check_and_notify_chef(chef_email, recipename)

        flash('Recipe purchased successfully!', 'success')
        return redirect(url_for('main.my_recipes'))

    return render_template(
        'buy_recipe.html',
        recipe=recipe,
        ingredients_list=ingredients_list,
        reviews=reviews,
        related_recipes=related_recipes
    )


@main.route('/add_review/<recipename>', methods=['GET', 'POST'])
def add_review(recipename):
    if 'email' not in session:
        flash('You need to log in to add a review.', 'danger')
        return redirect(url_for('main.login'))

    recipe = Recipe.query.filter_by(recipename=recipename).first()
    if not recipe:
        flash('Recipe not found.', 'danger')
        return redirect(url_for('main.my_recipes'))

    transaction = Transaction.query.filter_by(
        recipename=recipename,
        consumer_email=session['email']
    ).first()

    if not transaction:
        flash('No transaction found for this recipe.', 'danger')
        return redirect(url_for('main.my_recipes'))

    chef_email = recipe.chef_email

    if request.method == 'POST':
        rating = request.form.get('rating')
        comment = request.form.get('comment')

        if not rating or not comment:
            flash('All fields are required.', 'danger')
            return redirect(url_for('main.add_review', recipename=recipename))

        try:
            new_review = Review(
                comment=comment,
                rating=int(rating),
                consumer_email=session['email'],
                recipename=recipename,
                chef_email=chef_email,
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

            selected_allergens = request.form.getlist('allergiesrec[]')
            recipe.allergiesrec = ', '.join(selected_allergens)

            preparation_steps = request.form.getlist('preparation_steps[]')
            recipe.preparation = '|'.join([step.strip() for step in preparation_steps if step.strip()])

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

            if form.image.data:
                upload_folder = os.path.join(current_app.root_path, 'static/images')
                os.makedirs(upload_folder, exist_ok=True)

                image_file = form.image.data
                filename = secure_filename(image_file.filename)
                file_path = os.path.join(upload_folder, filename)
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
    user = User.query.filter_by(email=session.get('email')).first()

    if not user:
        flash('Please log in to access your profile.', 'danger')
        return redirect(url_for('main.login'))

    form = EditProfileForm(obj=user)

    form.allergies.choices = [(a, a) for a in get_allergens()]
    form.favorite_origins.choices = [(o, o) for o in get_origins()]

    preferences = user.preferences or {
        'allergies': [],
        'favorite_ingredients': [],
        'favorite_origins': []
    }

    if request.method == 'GET':
        form.allergies.data = preferences.get('allergies', [])
        form.favorite_ingredients.data = '\n'.join(preferences.get('favorite_ingredients', []))
        form.favorite_origins.data = preferences.get('favorite_origins', [])

    if form.validate_on_submit():
        try:
            user.name = form.name.data or user.name
            user.date_of_birth = form.date_of_birth.data or user.date_of_birth
            user.street = form.street.data or user.street
            user.housenr = form.housenr.data or user.housenr
            user.postalcode = form.postalcode.data or user.postalcode
            user.city = form.city.data or user.city
            user.country = form.country.data or user.country
            user.telephonenr = form.telephonenr.data or user.telephonenr

            new_ingredients = [ingredient.strip() for ingredient in form.favorite_ingredients.data.split('\n') if ingredient.strip()]

            updated_preferences = {
                'allergies': form.allergies.data,
                'favorite_ingredients': new_ingredients,
                'favorite_origins': form.favorite_origins.data
            }
            user.preferences = updated_preferences

            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('main.dashboard'))

        except Exception as e:
            db.session.rollback()
            flash(f"Error updating profile: {e}", 'danger')

    return render_template('edit_profile.html', form=form, user=user)


@main.route('/recipe_reviews/<recipename>')
def recipe_reviews(recipename):
    recipe = Recipe.query.filter_by(recipename=recipename).first()
    if not recipe:
        flash('Recipe not found.', 'danger')
        return redirect(url_for('main.dashboard'))

    reviews = Review.query.filter_by(recipename=recipename).all()

    avg_rating = (
        db.session.query(func.avg(Review.rating))
        .filter(Review.recipename == recipename)
        .scalar()
    )
    avg_rating = round(avg_rating, 1) if avg_rating else None

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

    return render_template(
        'recipe_reviews.html',
        recipe=recipe,
        reviews=reviews,
        avg_rating=avg_rating,
        ingredients_list=ingredients_list
    )


@chatbot.route('/chat', methods=['GET', 'POST'])
def chat():
    if request.method == 'POST':
        try:
            user_message = request.json.get('message', '').strip()
            print(f"User message: {user_message}")
            response = get_response(user_message)
            print(f"Chatbot response: {response}")
            return jsonify({"response": response}), 200
        except Exception as e:
            print(f"Error in chatbot: {e}")
            return jsonify({"response": "There was an error processing your request. Please try again later."}), 500

    return render_template('chatbot.html')


@main.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        try:
            name = form.name.data
            email = form.email.data
            subject = form.subject.data
            message = form.message.data
            is_public = form.is_public.data

            new_feedback = Feedback(
                name=name,
                email=email,
                subject=subject,
                message=message,
                is_public=is_public
            )
            db.session.add(new_feedback)
            db.session.commit()

            msg = Message(
                subject=f"New Message from {name}: {subject}",
                recipients=["dishcovery101@gmail.com"],  # Replace with your email
                body=f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}"
            )
            mail.send(msg)

            flash("Thank you for contacting us! We'll get back to you shortly.", "success")
            return redirect(url_for('main.contact'))

        except Exception as e:
            db.session.rollback()
            flash("An error occurred while submitting your message. Please try again.", "danger")
            print(f"Error: {e}")

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
