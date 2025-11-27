from fastapi.testclient import TestClient
from main import app
from auth import verify_token

# Désactiver le token
app.dependency_overrides[verify_token] = lambda: True

client = TestClient(app)


def test_root_endpoint():
    res = client.get("/")

    assert res.status_code == 200, (
        f"Le endpoint / aurait dû retourner 200.\n"
        f"Reçu : {res.status_code}"
    )

    data = res.json()

    # Vérification du champ "status"
    expected_status = "OK"
    received_status = data.get("status")

    assert received_status == expected_status, (
        "Valeur incorrecte pour 'status'.\n"
        f"  Attendu : {expected_status}\n"
        f"  Reçu    : {received_status}"
    )

    # Vérification du message
    expected_message_part = "API is running"
    received_message = data.get("message", "")

    assert expected_message_part in received_message, (
        "Le message du endpoint / ne contient pas la chaîne attendue.\n"
        f"  Attendu (partiel) : {expected_message_part}\n"
        f"  Reçu              : {received_message}"
    )
