from app.models import Recipe

import nltk
from nltk.stem import PorterStemmer
from app.models import Recipe, User
from sqlalchemy import func, cast, String

# Zorg ervoor dat NLTK de benodigde data downloadt
nltk.download('punkt')

# Initialiseer de stemmer
stemmer = PorterStemmer()

def apply_search(query, search_term):
    """
    Past een zoekbalkfilter toe op een query, inclusief het matchen van gestemde woorden.

    Parameters:
        query (SQLAlchemy Query): De query waarop het zoekfilter wordt toegepast.
        search_term (str): De zoekterm ingevoerd door de gebruiker.

    Returns:
        SQLAlchemy Query: De query met het zoekfilter toegepast.
    """
    if search_term:
        search_term = search_term.lower().strip()

        # Stem de zoekterm naar de basisvorm
        stemmed_term = stemmer.stem(search_term)

        query = query.join(User, User.email == Recipe.chef_email)

        query = query.filter(
            func.lower(Recipe.recipename).like(f"%{search_term}%") |
            func.lower(Recipe.recipename).like(f"%{stemmed_term}%") |
            func.lower(cast(Recipe.ingredients, String)).like(f"%{search_term}%") |
            func.lower(cast(Recipe.ingredients, String)).like(f"%{stemmed_term}%") |
            func.lower(Recipe.description).like(f"%{search_term}%") |
            func.lower(Recipe.description).like(f"%{stemmed_term}%") |
            func.lower(Recipe.category).like(f"%{search_term}%") |
            func.lower(Recipe.category).like(f"%{stemmed_term}%") |
            func.lower(Recipe.origin).like(f"%{search_term}%") |
            func.lower(Recipe.origin).like(f"%{stemmed_term}%") |
            func.lower(User.name).like(f"%{search_term}%") |  # Zoek op chef's naam
            func.lower(User.name).like(f"%{stemmed_term}%")   # Gestemde vorm van de naam
        )
    return query


