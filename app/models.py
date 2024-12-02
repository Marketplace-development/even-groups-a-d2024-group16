from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'User'

    email = db.Column(db.String, primary_key=True, unique=True, nullable=False)
    name = db.Column(db.String(80), nullable=False)
    date_of_birth = db.Column(db.DateTime, nullable=True)
    street = db.Column(db.String, nullable=True)
    housenr = db.Column(db.Integer, nullable=True)
    postalcode = db.Column(db.Integer, nullable=True)
    city = db.Column(db.String, nullable=True)
    country = db.Column(db.String, nullable=True)
    telephonenr = db.Column(db.String, nullable=True)
    is_chef = db.Column(db.Boolean, default=False, nullable=False)  # Gebruiker kan optioneel een chef zijn

    # Relationships
    recipes = db.relationship('Recipe', backref='chef', lazy=True, foreign_keys='Recipe.chef_email')
    transactions = db.relationship('Transaction', backref='User', lazy=True, foreign_keys='Transaction.consumer_email')
    
    def __repr__(self):
        return f"<User(name={self.name}, email={self.email})>"


class Recipe(db.Model):
    __tablename__ = 'recipe'

    recipename = db.Column(db.String, nullable=False)
    chef_email = db.Column(db.String, db.ForeignKey('User.email'), nullable=False)  # Verwijzing naar user.email (chef)
    description = db.Column(db.String, nullable=True)
    duration = db.Column(db.Integer, nullable=True)
    price = db.Column(db.String, nullable=True)
    ingredients = db.Column(db.String, nullable=True)
    allergiesrec = db.Column(db.String, nullable=True)
    image = db.Column(db.Text, nullable=True)

    # Maak de combinatie van recipename en chef_email de primaire sleutel
    __table_args__ = (
        db.PrimaryKeyConstraint('recipename', 'chef_email'),
    )

    # Relationships
    transactions = db.relationship('Transaction', backref='recipe', lazy=True)

    def __repr__(self):
        return f"<Recipe(recipename={self.recipename}, chef_email={self.chef_email})>"


class Transaction(db.Model):
    __tablename__ = 'transaction'

    transactionid = db.Column(db.Integer, primary_key=True)
    transactiondate = db.Column(db.DateTime, nullable=False)
    price = db.Column(db.String, nullable=False)
    consumer_email = db.Column(db.String, db.ForeignKey('User.email'), nullable=False)  # Foreign key naar User (consument)
    chef_email = db.Column(db.String, db.ForeignKey('User.email'), nullable=False)  # Foreign key naar User (chef)
    recipename = db.Column(db.String, db.ForeignKey('recipe.recipename'), nullable=False)

    # Relationships
    reviews = db.relationship('Review', backref='transaction', lazy=True)

    def __repr__(self):
        return f"<Transaction(transactionid={self.transactionid}, price={self.price})>"


class Review(db.Model):
    __tablename__ = 'review'

    reviewid = db.Column(db.Integer, primary_key=True)
    comment = db.Column(db.String, nullable=True)
    rating = db.Column(db.Integer, nullable=False)
    reviewdate = db.Column(db.DateTime, nullable=False)
    transactionid = db.Column(db.Integer, db.ForeignKey('transaction.transactionid'), nullable=False)

    # Constraints
    __table_args__ = (
        CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating_between_1_and_5'),
    )

    def __repr__(self):
        return f"<Review(reviewid={self.reviewid}, rating={self.rating})>"

