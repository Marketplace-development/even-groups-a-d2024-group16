from sqlalchemy import func, case, cast, Float
from app.models import Recipe, Review

def apply_sorting(query, sort_by):
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
            .order_by(
                case(
                    (avg_rating.isnot(None), avg_rating),  # Positieargumenten voor voorwaarden
                    else_=0  # Null beoordelingen krijgen prioriteit 0
                ).desc()
            )
        )
    elif sort_by == "prep_time_asc":
        query = query.order_by(Recipe.duration.asc())
    elif sort_by == "prep_time_desc":
        query = query.order_by(Recipe.duration.desc())
    elif sort_by == 'price_quality':
        # Bereken prijs-kwaliteitverhouding: prijs gedeeld door gemiddelde rating
        avg_rating = func.avg(Review.rating)
        price_quality_ratio = case(
            (avg_rating > 0, cast(Recipe.price, Float) / avg_rating),  # Alleen delen als rating > 0
            else_=None  # Recepten zonder rating krijgen geen waarde
        )
        query = (
            query.outerjoin(Review)
            .group_by(Recipe.recipename, Recipe.chef_email)
            .order_by(price_quality_ratio.asc())  # Laagste prijs-kwaliteitverhouding eerst
        )
    return query
