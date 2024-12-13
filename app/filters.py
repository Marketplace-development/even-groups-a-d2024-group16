from app.models import Recipe
from sqlalchemy import and_, not_, or_
import json

def apply_filters(query, filters):
    """Apply filters to the query."""
    # Ingrediëntenfilter
    if 'ingredients' in filters and filters['ingredients']:
        ingredients = filters['ingredients']
        query = query.filter(
            or_(*[Recipe.ingredients.contains({ingredient: {}}) for ingredient in ingredients])
        )

    # Allergieënfilter
    if 'allergies' in filters and filters['allergies']:
        allergies = filters['allergies']
        for allergy in allergies:
            query = query.filter(~Recipe.allergiesrec.ilike(f"%{allergy}%"))

    # Duurfilter
    if 'duration' in filters and filters['duration']:
        query = query.filter(Recipe.duration <= int(filters['duration']))

    # Prijsfilter
    if 'price' in filters and filters['price']:
        query = query.filter(Recipe.price <= float(filters['price']))

    # Categoriefilter
    if 'category' in filters and filters['category']:
        query = query.filter(Recipe.category == filters['category'])

    # Herkomstfilter
    if 'origin' in filters and filters['origin']:
        query = query.filter(Recipe.origin == filters['origin'])

    return query
