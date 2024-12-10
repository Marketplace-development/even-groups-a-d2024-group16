from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKeyConstraint, PrimaryKeyConstraint, CheckConstraint, Numeric
from sqlalchemy.dialects.postgresql import JSONB

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'User'

    email = db.Column(db.String, primary_key=True, unique=True, nullable=False)
    name = db.Column(db.String, nullable=False)
    date_of_birth = db.Column(db.DateTime, nullable=True)
    street = db.Column(db.String, nullable=True)
    housenr = db.Column(db.Integer, nullable=True)
    postalcode = db.Column(db.Integer, nullable=True)
    city = db.Column(db.String, nullable=True)
    country = db.Column(db.String, nullable=True)
    telephonenr = db.Column(db.String, nullable=True)
    is_chef = db.Column(db.Boolean, default=False, nullable=False)

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

    def __repr__(self):
        return f"<User(email={self.email}, name={self.name})>"

class Recipe(db.Model):
    __tablename__ = 'recipe'

    recipename = db.Column(db.String, primary_key=True)
    chef_email = db.Column(db.String, db.ForeignKey('User.email', ondelete='CASCADE'), primary_key=True)
    description = db.Column(db.String, nullable=True)
    duration = db.Column(db.Integer, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    ingredients = db.Column(JSONB, nullable=True)
    allergiesrec = db.Column(db.String, nullable=True)
    image = db.Column(db.Text, nullable=True)

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
    chef_email = db.Column(db.String, db.ForeignKey('User.email', ondelete='SET NULL'), nullable=True)
    recipename = db.Column(db.String, nullable=False)

    __table_args__ = (
        db.ForeignKeyConstraint(
            ['recipename', 'chef_email'],
            ['recipe.recipename', 'recipe.chef_email'],
            ondelete='SET NULL'
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
