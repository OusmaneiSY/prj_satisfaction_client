from fastapi import FastAPI, Depends
from pydantic import BaseModel
from typing import Optional, List

from auth import verify_token
from search_client import fetch_comments
from ml.scripts.model_loader import load_model
from ml.scripts.inference import predict_sentiment


# ===============================================================
# ===================  INITIALISATION API =======================
# ===============================================================

app = FastAPI(
    title="Sentiment Analysis API",
    description="API pour analyser et récupérer les avis clients",
    version="1.0.0",
)

# Chargement du modèle ML (UNE SEULE FOIS)
model = load_model()



# ===============================================================
# ===================  SCHEMAS ==================================
# ===============================================================

class PredictRequest(BaseModel):
    text: str
    company_name: Optional[str] = None


class PredictResponse(BaseModel):
    sentiment: str
    cleaned_text: str


class Comment(BaseModel):
    headline: Optional[str]
    review: Optional[str]
    rating: Optional[float]
    review_date_absolute: Optional[str]


class CommentsResponse(BaseModel):
    company: str
    count: int
    comments: List[Comment]



# ===============================================================
# ===============  ENDPOINT : HEALTH CHECK ======================
# ===============================================================

@app.get("/")
def root():
    return {"status": "OK", "message": "Sentiment Analysis API is running"}



# ===============================================================
# ==============  ENDPOINT : PREDICTION DE SENTIMENT ============
# ===============================================================

@app.post("/predict", response_model=PredictResponse)
def predict(payload: PredictRequest, authorized: bool = Depends(verify_token)):
    """
    Retourne le sentiment (positif / négatif / neutre)
    ainsi que le texte nettoyé utilisé par le modèle.
    """
    
    sentiment, cleaned_text = predict_sentiment(
        model,
        payload.text,
        payload.company_name
    )

    return PredictResponse(
        sentiment=sentiment,
        cleaned_text=cleaned_text
    )



# ===============================================================
# ==  ENDPOINT : RÉCUPÉRATION DES COMMENTAIRES ELASTICSEARCH ====
# ===============================================================

@app.get("/comments", response_model=CommentsResponse)
def list_comments(
    company_name: str,
    limit: int = 20,
    authorized: bool = Depends(verify_token)
):
    """
    Récupère les derniers commentaires d’une entreprise
    depuis Elasticsearch.
    """

    comments = fetch_comments(company_name, size=limit)

    return CommentsResponse(
        company=company_name,
        count=len(comments),
        comments=comments
    )
