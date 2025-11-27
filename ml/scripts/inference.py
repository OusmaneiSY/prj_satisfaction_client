from .preprocessing import clean_advanced, build_stopwords

def predict_sentiment(model, text: str, company_name: str | None):
    """
    Prépare les stopwords dynamiques, nettoie le texte et retourne
    à la fois la prédiction et le texte nettoyé.
    """
    
    # stopwords dynamiques selon company_name
    stopwords = build_stopwords(company_name)

    # nettoyage avancé
    cleaned = clean_advanced(text, company_name, stopwords)

    # prédiction
    pred = model.predict([cleaned])[0]

    # retourne prédiction + texte nettoyé
    return pred, cleaned
