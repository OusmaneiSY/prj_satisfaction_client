import re
import spacy
from spacy.lang.fr.stop_words import STOP_WORDS

# Charger spaCy une seule fois
nlp = spacy.load("fr_core_news_md")


def load_company_stopwords(company_name: str):
    """
    Transforme le nom d'entreprise en stopwords
    (utile si tu veux retirer automatiquement ce nom du texte)
    Exemple :
        "Amazon Prime" -> {"amazon", "prime", "amazon prime"}
    """
    if not company_name:
        return set()

    company_name = company_name.lower()

    tokens = set()
    tokens.add(company_name)

    for t in company_name.split():
        tokens.add(t)

    return tokens


def build_stopwords(company_name: str = None):
    """
    Construit la liste finale des stopwords :
      - stopwords français spaCy
      - mots composant le company_name
    """
    stopwords = set(STOP_WORDS)

    # Ajouter les tokens du nom d'entreprise
    company_tokens = load_company_stopwords(company_name)
    stopwords |= company_tokens

    return stopwords


def clean_advanced(text: str, company_name: str | None, stopwords: set[str]) -> str:
    """
    Nettoyage avancé :
      - lowercase
      - suppression du nom de l'entreprise
      - regex (identique au notebook)
      - spaCy pour lemmatisation
      - suppression stopwords
    """

    # 1) lowercase
    text = text.lower()

    # 2) supprimer le nom complet + tokens individuels
    if company_name:
        company_name = company_name.lower()
        text = text.replace(company_name, "")
        for token in company_name.split():
            text = text.replace(token, "")

    # 3) nettoyer caractères spéciaux — version EXACTE de ton notebook
    text = re.sub(r"[^a-zA-Z0-9À-ÿ ]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    # 4) spaCy
    doc = nlp(text)
    cleaned_tokens = []

    for token in doc:
        lemma = token.lemma_.strip()

        if len(lemma) < 3:
            continue
        if lemma in stopwords:
            continue

        cleaned_tokens.append(lemma)

    return " ".join(cleaned_tokens)
