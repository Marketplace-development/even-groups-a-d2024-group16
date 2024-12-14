from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import text, cast
from app.models import Recipe

def apply_filters(query, filters):
    """Past filters toe op ingrediënten en allergieën."""
    
    # Filter op ingrediënten (recept moet ALLE ingrediënten bevatten)
    if filters.get('ingredients'):
        ingredients = filters['ingredients']
        query = query.filter(
            Recipe.ingredients.op('@>')(cast(ingredients, JSONB))
        )

    # Filter op allergieën (recept mag GEEN van de allergieën bevatten)
    if filters.get('allergies'):
        allergies = filters['allergies']
        query = query.filter(
            ~Recipe.allergiesrec.op('?|')(cast(allergies, JSONB))
        )

    # Andere filters blijven hetzelfde
    if filters.get('origin'):
        query = query.filter(Recipe.origin == filters['origin'])

    if filters.get('category'):
        query = query.filter(Recipe.category == filters['category'])

    if filters.get('min_rating'):
        min_rating = float(filters['min_rating'])
        query = query.filter(
            func.coalesce(func.avg(Review.rating), 0) >= min_rating
        )

    if filters.get('price'):
        max_price = float(filters['price'])
        query = query.filter(Recipe.price <= max_price)

    if filters.get('duration'):
        max_duration = int(filters['duration'])
        query = query.filter(Recipe.duration <= max_duration)

    return query
