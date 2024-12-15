from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKeyConstraint, PrimaryKeyConstraint, CheckConstraint, Numeric
from sqlalchemy.dialects.postgresql import JSONB, NUMERIC

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'User'

    email = db.Column(db.String, primary_key=True, unique=True, nullable=False)
    name = db.Column(db.String, nullable=False)
    date_of_birth = db.Column(db.DateTime, nullable=True)
    street = db.Column(db.String, nullable=True)
    housenr = db.Column(db.Integer, nullable=True)
    postalcode = db.Column(db.String, nullable=True)  # Veranderd naar String voor compatibiliteit met internationale postcodes
    city = db.Column(db.String, nullable=True)
    country = db.Column(db.String, nullable=True)
    telephonenr = db.Column(db.String, nullable=True)
    is_chef = db.Column(db.Boolean, default=False, nullable=False)  # Nodig om te onderscheiden tussen chefs en klanten
    preferences = db.Column(db.JSON, nullable=True, default={})  # Sla voorkeuren op als JSON met standaardwaarde {}

    # Relaties
    recipes = db.relationship('Recipe', backref='chef', lazy=True)
    consumer_transactions = db.relationship(
        'Transaction',
        backref='consumer',
        lazy=True,
        primaryjoin="User.email == Transaction.consumer_email"
    )
    chef_transactions = db.relationship(
        'Transaction',
        backref='chef_user',
        lazy=True,
        primaryjoin="User.email == Transaction.chef_email"
    )

    def set_preferences(self, favorite_ingredients=None, favorite_origins=None, allergies=None):
        """
        Update user preferences.
        """
        self.preferences = {
            "favorite_ingredients": favorite_ingredients or [],
            "favorite_origins": favorite_origins or [],
            "allergies": allergies or [],
        }

    def get_preferences(self):
        """
        Retrieve user preferences.
        """
        return self.preferences or {}

    def __repr__(self):
        return f"<User(email={self.email}, name={self.name}, is_chef={self.is_chef})>"


class Recipe(db.Model):
    __tablename__ = 'recipe'

    recipename = db.Column(db.String, nullable=False)
    chef_email = db.Column(db.String, db.ForeignKey('User.email', ondelete='CASCADE'), nullable=False)
    chef_name = db.Column(db.String, nullable=False)  # Toegevoegd om overeen te komen met SQL-schema
    description = db.Column(db.String, nullable=True)
    duration = db.Column(db.Integer, nullable=True)
    price = db.Column(NUMERIC(10, 2), nullable=True)  # Wijziging naar NUMERIC voor prijs met decimalen
    ingredients = db.Column(JSONB, nullable=True)  # Blijft als JSONB zoals het oorspronkelijk was
    allergiesrec = db.Column(db.Text, nullable=True)
    image = db.Column(db.Text, nullable=True)
    origin = db.Column(db.String, nullable=True)  # Toegevoegd voor herkomst
    category = db.Column(db.String, nullable=True)  # Toegevoegd voor categorie
    preparation = db.Column(db.Text, nullable=True)  # Toegevoegd voor bereidingswijze

    __table_args__ = (
        PrimaryKeyConstraint('recipename', 'chef_email'),
    )

    def __repr__(self):
        return f"<Recipe(recipename={self.recipename}, chef_email={self.chef_email})>"



class Transaction(db.Model):
    __tablename__ = 'transaction'

    transactionid = db.Column(db.BigInteger, primary_key=True)
    transactiondate = db.Column(db.DateTime, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    consumer_email = db.Column(db.String, db.ForeignKey('User.email', ondelete='SET NULL'), nullable=True)
    chef_email = db.Column(db.String, db.ForeignKey('User.email', ondelete='SET NULL'), nullable=False)
    recipename = db.Column(db.String, nullable=False)

    __table_args__ = (
        db.ForeignKeyConstraint(
            ['recipename', 'chef_email'],
            ['recipe.recipename', 'recipe.chef_email'],
            ondelete='CASCADE'
        ),
    )

    def __repr__(self):
        return f"<Transaction(transactionid={self.transactionid}, recipename={self.recipename})>"





class Review(db.Model):
    __tablename__ = 'review'

    reviewid = db.Column(db.BigInteger, primary_key=True)
    comment = db.Column(db.Text, nullable=True)
    rating = db.Column(db.Integer, nullable=False)
    reviewdate = db.Column(db.DateTime, default=db.func.current_timestamp())
    consumer_email = db.Column(db.String, db.ForeignKey('User.email', ondelete='SET NULL'), nullable=False)
    recipename = db.Column(db.String, nullable=False)
    chef_email = db.Column(db.String, nullable=False)
    transactionid = db.Column(db.BigInteger, db.ForeignKey('transaction.transactionid', ondelete='CASCADE'), nullable=False)

    __table_args__ = (
        db.ForeignKeyConstraint(
            ['recipename', 'chef_email'],
            ['recipe.recipename', 'recipe.chef_email'],
            ondelete='CASCADE'
        ),
        db.CheckConstraint('rating BETWEEN 1 AND 5', name='check_rating_range'),
    )

    def __repr__(self):
        return f"<Review(reviewid={self.reviewid}, rating={self.rating})>"

