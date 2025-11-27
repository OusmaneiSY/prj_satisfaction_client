from fastapi.testclient import TestClient
from unittest.mock import patch

from main import app
from auth import verify_token

# Désactivation du token
app.dependency_overrides[verify_token] = lambda: True

client = TestClient(app)


@patch("main.fetch_comments")   # On mocke l'instance utilisée dans main.py
def test_comments_endpoint(mock_fetch):
    # Fake data simulant Elasticsearch
    fake_comments = [
        {
            "headline": "Excellent produit",
            "review": "Vraiment très satisfait",
            "rating": 5.0,
            "review_date_absolute": "2024-10-01"
        },
        {
            "headline": "Pas terrible",
            "review": "Déçu de la qualité",
            "rating": 2.0,
            "review_date_absolute": "2024-10-02"
        }
    ]

    mock_fetch.return_value = fake_comments

    response = client.get("/comments?company_name=TestCorp&limit=10")

    # Vérification du status code
    assert response.status_code == 200, (
        "Status code incorrect pour /comments.\n"
        f"  Attendu : 200\n"
        f"  Reçu    : {response.status_code}"
    )

    data = response.json()

    # Vérification du champ company 
    expected_company = "TestCorp"
    received_company = data.get("company")

    assert received_company == expected_company, (
        "Valeur incorrecte pour 'company'.\n"
        f"  Attendu : {expected_company}\n"
        f"  Reçu    : {received_company}"
    )

    # Vérification du count
    expected_count = 2
    received_count = data.get("count")

    assert received_count == expected_count, (
        "Valeur incorrecte pour 'count'.\n"
        f"  Attendu : {expected_count}\n"
        f"  Reçu    : {received_count}"
    )

    # Vérification des commentaires
    comments = data.get("comments", [])
    assert len(comments) == 2, (
        "Nombre incorrect de commentaires renvoyés.\n"
        f"  Attendu : 2\n"
        f"  Reçu    : {len(comments)}"
    )

    # Vérification du premier commentaire 
    expected_headline = "Excellent produit"
    received_headline = comments[0].get("headline")

    assert received_headline == expected_headline, (
        "Valeur incorrecte pour le premier 'headline'.\n"
        f"  Attendu : {expected_headline}\n"
        f"  Reçu    : {received_headline}"
    )
