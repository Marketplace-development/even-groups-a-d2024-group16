from app.models import Recipe

from sqlalchemy import func, cast, String

def apply_search(query, search_term):
    """
    Past een zoekbalkfilter toe op een query.

    Parameters:
        query (SQLAlchemy Query): De query waarop het zoekfilter wordt toegepast.
        search_term (str): De zoekterm ingevoerd door de gebruiker.

    Returns:
        SQLAlchemy Query: De query met het zoekfilter toegepast.
    """
    if search_term:
        search_term = search_term.lower().strip()
        query = query.filter(
            func.lower(Recipe.recipename).like(f"%{search_term}%") |
            func.lower(cast(Recipe.ingredients, String)).like(f"%{search_term}%") |
            func.lower(Recipe.description).like(f"%{search_term}%") |
            func.lower(Recipe.category).like(f"%{search_term}%") |
            func.lower(Recipe.origin).like(f"%{search_term}%")
        )
    return query

