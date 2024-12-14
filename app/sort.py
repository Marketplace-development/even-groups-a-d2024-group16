from sqlalchemy import func, case, cast, Float
from app.models import Recipe, Review
from sqlalchemy import func, case, cast, Float
from sqlalchemy import func, case, cast, Float
from sqlalchemy import func, case, Float

def apply_sorting(query, sort_by, preferences=None):
    """Pas de sorteervolgorde toe."""
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
            (avg_rating > 0, Recipe.price / avg_rating),  # Bereken prijs-kwaliteitverhouding
            else_=float('inf')  # Recepten zonder beoordeling krijgen een hoge waarde
        )
        query = (
            query.outerjoin(Review)
            .group_by(Recipe.recipename, Recipe.chef_email)
            .order_by(price_quality_ratio.asc())
        )
    elif sort_by == 'recommended' and preferences:
        # Sorteren op basis van favorite_origins
        favorite_origins = preferences.get('favorite_origins', [])
        
        if favorite_origins:  # Alleen sorteren als er voorkeuren zijn
            origin_match = func.sum(
                case(
                    (Recipe.origin.in_(favorite_origins), 1),
                    else_=0
                )
            )
            query = (
                query.outerjoin(Review)
                .group_by(Recipe.recipename, Recipe.chef_email)
                .order_by(origin_match.desc())  # Prioriteer recepten die overeenkomen met favorite_origins
            )
        else:
            # Als er geen voorkeuren zijn, sorteer op gemiddelde beoordeling
            avg_rating = func.avg(Review.rating)
            query = (
                query.outerjoin(Review)
                .group_by(Recipe.recipename, Recipe.chef_email)
                .order_by(avg_rating.desc())
            )
    else:
        # Standaard sortering (bijvoorbeeld prijs-kwaliteitverhouding)
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
