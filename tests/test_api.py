# tests/test_api.py

from fastapi.testclient import TestClient
from app.main import app
import pytest

client = TestClient(app)

@pytest.fixture(scope="module")
def test_user_token():
    # Définir les informations d'identification de l'utilisateur de test
    user_data = {"username": "testuser", "password": "testpassword"}

    # Créer un nouvel utilisateur
    response = client.post("/users/", json=user_data)
    assert response.status_code in [200, 400], "Échec de la création de l'utilisateur"

    # Authentifier l'utilisateur pour obtenir un jeton
    response = client.post("/token", data={"username": user_data["username"], "password": user_data["password"]})
    assert response.status_code == 200, "Échec de la récupération du jeton"

    token = response.json().get("access_token")
    assert token is not None, "Aucun jeton d'accès retourné"

    return token

def test_predict_endpoint(test_user_token):
    response = client.post(
        "/predict",
        json={"features": [5.1, 3.5, 1.4, 0.2]},
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 200, f"Attendu 200, obtenu {response.status_code}"
    json_response = response.json()
    assert "prediction" in json_response, "Clé 'prediction' manquante dans la réponse"
    assert "prediction_time_seconds" in json_response, "Clé 'prediction_time_seconds' manquante dans la réponse"
    assert isinstance(json_response["prediction_time_seconds"], float), "'prediction_time_seconds' n'est pas un float"

def test_predict_endpoint_missing_feature(test_user_token):
    response = client.post(
        "/predict",
        json={"features": [5.1, 3.5, 1.4]},  # Manque une feature
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 422, f"Attendu 422, obtenu {response.status_code}"
    assert response.json()["detail"][0]["msg"] == "Le nombre de features doit être exactement 4.", "Message d'erreur inattendu pour les features manquantes"

def test_predict_endpoint_feature_out_of_range(test_user_token):
    response = client.post(
        "/predict",
        json={"features": [5.1, 3.5, 1.4, -1.0]},  # Feature négative
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 422, f"Attendu 422, obtenu {response.status_code}"
    assert response.json()["detail"][0]["msg"] == "ensure this value is greater than or equal to 0", "Message d'erreur inattendu pour les features hors plage"
