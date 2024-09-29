# tests/test_api.py

from fastapi.testclient import TestClient
from app.main import app, get_current_user
from app.database import User as DBUser

# Override de la dépendance pour bypasser l'authentification
def override_get_current_user():
    return DBUser(id=1, username='testuser', hashed_password='fakehashedpassword')

app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(app)

def test_predict_endpoint():
    response = client.post(
        "/predict",
        json={"features": [5.1, 3.5, 1.4, 0.2]},
    )
    assert response.status_code == 200
    json_response = response.json()
    assert "prediction" in json_response
    assert "prediction_time_seconds" in json_response
    assert isinstance(json_response["prediction_time_seconds"], float)

def test_predict_endpoint_missing_feature():
    response = client.post(
        "/predict",
        json={"features": [5.1, 3.5, 1.4]},  # Manque une feature
    )
    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] == "ensure this value has at least 4 items"


def test_predict_endpoint_feature_out_of_range():
    response = client.post(
        "/predict",
        json={"features": [5.1, 3.5, 1.4, -1.0]},  # Feature négative
    )
    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"].startswith("ensure this value is greater than or equal to 0")
