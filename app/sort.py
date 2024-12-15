from sqlalchemy import func, case, cast, Text, Float
from app.models import Recipe, Review

def apply_sorting(query, sort_by, preferences=None):
    """Pas de sorteervolgorde toe, inclusief gebruikersvoorkeuren en allergieën."""
    if not preferences:
        preferences = {}

    # Haal voorkeuren en allergieën op uit de opgeslagen JSON
    allergies = preferences.get('allergies', [])
    favorite_origins = preferences.get('favorite_origins', [])
    favorite_ingredients = preferences.get('favorite_ingredients', [])

    if sort_by == 'price_low_to_high':
        query = query.order_by(Recipe.price.asc())
    elif sort_by == 'price_high_to_low':
        query = query.order_by(Recipe.price.desc())
    elif sort_by == 'rating_high_to_low':
        avg_rating = func.avg(Review.rating)
        query = (
            query.outerjoin(Review)
            .group_by(Recipe.recipename, Recipe.chef_email)
            .order_by(avg_rating.desc())
        )
    elif sort_by == "prep_time_asc":
        query = query.order_by(Recipe.duration.asc())
    elif sort_by == "prep_time_desc":
        query = query.order_by(Recipe.duration.desc())
    elif sort_by == 'price_quality':
        avg_rating = func.avg(Review.rating)
        price_quality_ratio = case(
            (avg_rating > 0, Recipe.price / avg_rating),
            else_=float('inf')  # Recepten zonder beoordeling krijgen een hoge waarde
        )
        query = (
            query.outerjoin(Review)
            .group_by(Recipe.recipename, Recipe.chef_email)
            .order_by(price_quality_ratio.asc())
        )
    elif sort_by == 'recommended':
        # Bereken prioriteit voor favoriete herkomsten
        origin_match = func.sum(
            case(
                (Recipe.origin.in_(favorite_origins), 1),
                else_=0
            )
        )

        # Bereken prioriteit voor favoriete ingrediënten
        ingredient_match = func.sum(
            case(
                *[
                    (func.lower(cast(Recipe.ingredients, Text)).like(f"%{ingredient.lower()}%"), 1)
                    for ingredient in favorite_ingredients
                ],
                else_=0
            )
        )

        # Filter recepten met allergieën
        if allergies:
            for allergy in allergies:
                query = query.filter(
                    ~func.lower(cast(Recipe.allergiesrec, Text)).like(f"%{allergy.lower()}%")
                )

        # Voeg fallback voor beoordelingen toe
        avg_rating = func.avg(Review.rating)

        # Combineer alle factoren voor sortering
        query = (
            query.outerjoin(Review)
            .group_by(Recipe.recipename, Recipe.chef_email)
            .order_by(
                origin_match.desc(),  # Prioriteer recepten met overeenkomende herkomsten
                ingredient_match.desc(),  # Prioriteer recepten met overeenkomende ingrediënten
                avg_rating.desc()  # Fallback naar beoordelingen
            )
        )
    else:
        # Standaard sortering: prijs-kwaliteitverhouding
        avg_rating = func.avg(Review.rating)
        price_quality_ratio = case(
            (avg_rating > 0, Recipe.price / avg_rating),
            else_=float('inf')
        )
        query = (
            query.outerjoin(Review)
            .group_by(Recipe.recipename, Recipe.chef_email)
            .order_by(price_quality_ratio.asc())
        )

    return query
