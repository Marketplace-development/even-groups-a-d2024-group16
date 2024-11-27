from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'user'

    userid = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, nullable=False, unique=True)
    name = db.Column(db.String(80), nullable=False)
    date_of_birth = db.Column(db.DateTime, nullable=True)  # Handles 'timestamp with time zone'
    street = db.Column(db.String, nullable=True)
    housenr = db.Column(db.Integer, nullable=True)
    postalcode = db.Column(db.Integer, nullable=True)
    city = db.Column(db.String, nullable=True)
    country = db.Column(db.String, nullable=True)
    telephonenr = db.Column(db.String, nullable=True)

    # Relationships
    consumer = db.relationship('Consumer', backref='User', uselist=False)
    chef = db.relationship('Chef', backref='User', uselist=False)

    def __repr__(self):
        return f"<User(name={self.name}, email={self.email})>"
    
class Dish(db.Model):
    __tablename__ = 'dish'

    dishid = db.Column(db.Integer, primary_key=True)
    dishtype = db.Column(db.String, nullable=False)  # Assumes this is required

    # Relationships
    recipes = db.relationship('Recipe', backref='Dish', lazy=True)

    def __repr__(self):
        return f"<Dish(dishid={self.dishid}, dishtype={self.dishtype})>"

class Chef(db.Model):
    __tablename__ = 'chef'

    chefid = db.Column(db.Integer, primary_key=True)
    avgrating = db.Column(db.String, nullable=True)  # Assuming stored as numeric
    userid = db.Column(db.Integer, db.ForeignKey('user.userid'), nullable=False)  # Foreign key to User

    # Relationships
    recipes = db.relationship('Recipe', backref='Chef', lazy=True)
    transactions = db.relationship('Transaction', backref='Chef', lazy=True)

    def __repr__(self):
        return f"<Chef(chefid={self.chefid}, avgrating={self.avgrating})>"


class Recipe(db.Model):
    __tablename__ = 'recipe'

    recipeid = db.Column(db.Integer, primary_key=True, nullable=False)
    chefid = db.Column(db.Integer, db.ForeignKey('Chef.chefid'), nullable=False)  # Foreign key to Chef
    dishid = db.Column(db.Integer, db.ForeignKey('Dish.dishid'), nullable=False)  # Foreign key to DishC
    description = db.Column(db.String, nullable=True)
    duration = db.Column(db.Integer, nullable=True)  # Assuming this is in minutes
    price = db.Column(db.String, nullable=True)  # Numeric stored as string for precision
    ingredients = db.Column(db.String, nullable=True)
    allergiesrec = db.Column(db.String, nullable=True)
    image = db.Column(db.String, nullable=True)
    

class Transaction(db.Model):
    __tablename__ = 'transaction'

    transactionid = db.Column(db.Integer, primary_key=True)
    transactiondate = db.Column(db.DateTime, nullable=False)  # Timestamp with time zone
    price = db.Column(db.String, nullable=False)  # Numeric stored as string
    consumerid = db.Column(db.Integer, db.ForeignKey('consumer.consumerid'), nullable=False)  # Foreign key to Consumer
    chefid = db.Column(db.Integer, db.ForeignKey('chef.chefid'), nullable=False)  # Foreign key to Chef

    # Relationships
    reviews = db.relationship('Review', backref='Transaction', lazy=True)

    def __repr__(self):
        return f"<Transaction(transactionid={self.transactionid}, price={self.price})>"

class Review(db.Model):
    __tablename__ = 'review'

    reviewid = db.Column(db.Integer, primary_key=True)
    comment = db.Column(db.String, nullable=True)
    rating = db.Column(db.Integer, nullable=False)  # Assuming this is an integer rating (e.g., 1-5)
    reviewdate = db.Column(db.DateTime, nullable=False)  # Timestamp with time zone
    transactionid = db.Column(db.Integer, db.ForeignKey('transaction.transactionid'), nullable=False)  # Foreign key to Transaction

    def __repr__(self):
        return f"<Review(reviewid={self.reviewid}, rating={self.rating})>"

class Consumer(db.Model):
    __tablename__ = 'consumer'

    consumerid = db.Column(db.Integer, primary_key=True)
    allergiescon = db.Column(db.String, nullable=True)
    fridgecontents = db.Column(db.String, nullable=True)
    userid = db.Column(db.Integer, db.ForeignKey('user.userid'), nullable=False)  # Foreign key to User

    # Relationships
    transactions = db.relationship('Transaction', backref='Consumer', lazy=True)

    def __repr__(self):
        return f"<Consumer(consumerid={self.consumerid})>"

