from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import text, cast
from app.models import Recipe

def apply_filters(query, filters):
    """Past filters toe op de receptenquery."""

    # Ingrediëntenfilter (reeds correct)
    if filters.get('ingredients'):
        ingredients = filters['ingredients']
        query = query.filter(
            Recipe.ingredients.op('@>')(cast(ingredients, JSONB))
        )

    # Allergieënfilter (reeds correct)
    if filters.get('allergies'):
        allergies = filters['allergies']
        query = query.filter(
            ~Recipe.allergiesrec.op('?|')(cast(allergies, JSONB))
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
    if filters.get('price'):
        try:
            max_price = float(filters['price'])
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
