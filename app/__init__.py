# app/__init__.py

from flask import Flask #import the Flask class
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from .config import Config #import Config class with information on login to Supabase
from .models import db

migrate = Migrate()

def create_app():
    app = Flask(__name__) #create an instance of the class
    app.config.from_object(Config) #updates the values fot the object Config

    db.init_app(app) #initialize the instance db with the Specific Flask instance "app"
    migrate.init_app(app,db)

    with app.app_context():
        from .routes import main
        app.register_blueprint(main)
    
    return app



    
