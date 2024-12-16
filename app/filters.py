from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import text, cast
from sqlalchemy import func
from app.models import Recipe

def apply_filters(query, filters):
    """Past filters toe op de receptenquery."""

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
