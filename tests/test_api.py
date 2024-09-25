from fastapi.testclient import TestClient
from app.main import app, create_db_and_tables
from app.database import get_db, User, SessionLocal, get_password_hash

client = TestClient(app)

def setup_module(module):
    # Créer la base de données de test
    create_db_and_tables()
    db = SessionLocal()
    # Ajouter un utilisateur de test
    test_user = User(
        username="testuser",
        hashed_password=get_password_hash("testpassword")
    )
    db.add(test_user)
    db.commit()
    db.close()

def test_token_endpoint():
    response = client.post(
        "/token",
        data={"username": "testuser", "password": "testpassword"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_predict_endpoint():
    # Obtenir le token
    token_response = client.post(
        "/token",
        data={"username": "testuser", "password": "testpassword"}
    )
    token = token_response.json()["access_token"]

    response = client.post(
        "/predict",
        json={"features": [5.1, 3.5, 1.4, 0.2]},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert "prediction" in response.json()

def test_predict_endpoint_invalid_input():
    # Obtenir le token
    token_response = client.post(
        "/token",
        data={"username": "testuser", "password": "testpassword"}
    )
    token = token_response.json()["access_token"]

    response = client.post(
        "/predict",
        json={"features": [1, 2, 3]},  # Invalid number of features
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400

def test_predict_endpoint_invalid_token():
    response = client.post(
        "/predict",
        json={"features": [5.1, 3.5, 1.4, 0.2]},
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401

def test_model_info_endpoint():
    # Obtenir le token
    token_response = client.post(
        "/token",
        data={"username": "testuser", "password": "testpassword"}
    )
    token = token_response.json()["access_token"]

    response = client.get(
        "/model-info",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert "model_name" in response.json()

def test_unauthorized_access():
    response = client.get("/model-info")
    assert response.status_code == 401
