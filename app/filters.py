from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import text, cast
from sqlalchemy import func, and_
from app.models import Recipe
from app import db  # SQLAlchemy-instantie

import json


def apply_filters(query, filters):
    """Past filters toe op de receptenquery."""
    if filters.get('ingredients') and filters['ingredients'] != '[]':
        try:
            ingredient_list = json.loads(filters['ingredients'])
            if ingredient_list:
                ingredient_conditions = [
                    func.lower(cast(Recipe.ingredients, db.Text)).like(f'%"{ingredient.lower()}"%')
                    for ingredient in ingredient_list
                ]
                query = query.filter(and_(*ingredient_conditions))  # Zorg dat alle ingrediënten aanwezig zijn
        except json.JSONDecodeError:
            pass  # Negeer ongeldige JSON

    # Allergieënfilter (recepten zonder de opgegeven allergieën)
    if filters.get('allergies'):
        allergy_filters = filters['allergies']
        for allergy in allergy_filters:
            query = query.filter(
                ~func.lower(Recipe.allergiesrec).like(f"%{allergy.lower()}%")
            )
    
    # Herkomstfilter
    if filters.get('origin'):
        origin = filters['origin'].strip()
        query = query.filter(Recipe.origin == origin)

    # Categoriefilter
    if filters.get('category'):
        category = filters['category'].strip()
        query = query.filter(Recipe.category == category)

    # Prijsfilter
    if filters.get('min_price'):
        try:
            min_price = float(filters['min_price'])
            query = query.filter(Recipe.price >= min_price)
        except ValueError:
            pass  # Negeer ongeldige invoer

    # Max Prijs filter
    if filters.get('max_price'):
        try:
            max_price = float(filters['max_price'])
            query = query.filter(Recipe.price <= max_price)
        except ValueError:
            pass  # Negeer ongeldige invoer

    # Bereidingstijdfilter
    if filters.get('duration'):
        try:
            max_duration = int(filters['duration'])
            query = query.filter(Recipe.duration <= max_duration)
        except ValueError:
            pass  # Negeer ongeldige invoer

    return query
