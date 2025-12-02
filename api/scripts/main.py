from fastapi import FastAPI, Depends
from pydantic import BaseModel
from typing import Optional, List, Literal
from datetime import date

from auth import verify_token
from search_client import fetch_comments
from ml.scripts.model_loader import load_model
from ml.scripts.inference import predict_sentiment
from fastapi import Query


# ===============================================================
# ===================  INITIALISATION API =======================
# ===============================================================

app = FastAPI(
    title="Sentiment Analysis API",
    description="API pour analyser et récupérer les avis clients",
    version="1.0.0",
)

model = load_model()


# ===============================================================
# =============== LISTES POUR LES DROPDOWNS SWAGGER =============
# ===============================================================

COMPANIES = [
    "showroomprive",
    "amazon",
    "apple",
    "aliexpress",
    "justfly",
    "westernunion",
    "loaded",
]

CompanyLiteral = Literal[tuple(COMPANIES)]



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
    company_name: CompanyLiteral,
    limit: int = Query(20, description="Nombre de commentaires à récupérer"),
    authorized: bool = Depends(verify_token)
):
    """
    Récupère les derniers commentaires d’une entreprise
    depuis Elasticsearch (sans filtre de dates).
    """

    comments = fetch_comments(
        company_name,
        size=limit
    )

    return CommentsResponse(
        company=company_name,
        count=len(comments),
        comments=comments
    )
