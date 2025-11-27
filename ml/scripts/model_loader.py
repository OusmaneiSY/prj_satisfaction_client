import joblib

def load_model():
    """
    Charge uniquement le modèle d'entraînement.
    Cette fonction est appelée UNE SEULE FOIS au démarrage de l'API.
    """
    model = joblib.load("/app/models/sentiment_best_linear_svc.pkl")
    return model
