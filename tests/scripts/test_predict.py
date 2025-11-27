from fastapi.testclient import TestClient
from main import app
from auth import verify_token

# Override du token
app.dependency_overrides[verify_token] = lambda: True

client = TestClient(app)


def test_predict_positive_sentiment():
    payload = {
        "text": "J'adore ce produit, il est excellent et je le recommande fortement.",
        "company_name": "TestCorp"
    }

    response = client.post("/predict", json=payload)

    assert response.status_code == 200
    data = response.json()

    # Vérifie les champs obligatoires
    assert "sentiment" in data
    assert "cleaned_text" in data

    # Valeur attendue
    expected = "positif"
    received = data["sentiment"].lower()

    # Vérifie que le sentiment est positif AVEC message clair
    assert received == expected, (
        f"Sentiment inattendu.\n"
        f"  Attendu : {expected}\n"
        f"  Reçu    : {received}\n"
        f"Payload   : {payload['text']}"
    )
