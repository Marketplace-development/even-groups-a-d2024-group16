from sqlalchemy import and_
from app.models import Recipe

def apply_filters(query, filters):
    """Apply filters to the query."""
    if 'ingredients' in filters and filters['ingredients']:
        ingredients = filters['ingredients'].split(',')
        query = query.filter(and_(*[Recipe.ingredients.op('@>')({'name': ingredient}) for ingredient in ingredients]))

    if 'duration' in filters and filters['duration']:
        query = query.filter(Recipe.duration <= int(filters['duration']))

    if 'price' in filters and filters['price']:
        query = query.filter(Recipe.price <= float(filters['price']))

    if 'category' in filters and filters['category']:
        query = query.filter(Recipe.category == filters['category'])

    if 'origin' in filters and filters['origin']:
        query = query.filter(Recipe.origin == filters['origin'])

    if 'allergies' in filters and filters['allergies']:
        query = query.filter(~Recipe.allergiesrec.contains(filters['allergies']))

    return query
