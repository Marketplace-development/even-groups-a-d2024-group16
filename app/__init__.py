# app/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from .config import Config
from .models import db


migrate = Migrate()
mail = Mail()

def create_app():
    app = Flask(__name__)  # Maak een nieuwe Flask-applicatie
    app.config.from_object(Config)  # Configureer de app met de waarden uit Config

    db.init_app(app)  # Initialiseer SQLAlchemy
    migrate.init_app(app, db)
    mail.init_app(app)# Initialiseer Flask-Migrate

    with app.app_context():
        from .routes import main, chatbot  # Importeer beide Blueprints vanuit routes.py

        # Registreer Blueprints
        app.register_blueprint(main)  # Hoofd-Blueprint
        app.register_blueprint(chatbot, url_prefix="/chatbot")  # Chatbot Blueprint

    return app
