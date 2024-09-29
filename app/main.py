from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Optional
import joblib
import os
from dotenv import load_dotenv

import logging
import mlflow
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
import time  # Import ajouté

load_dotenv()

app = FastAPI()

# CORS Middleware (optionnel, ajustez selon vos besoins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Changez ceci en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Définir l'URI de suivi MLflow
if os.environ.get('DOCKER_CONTAINER', False):
    mlflow_tracking_uri = os.getenv('MLFLOW_TRACKING_URI', 'http://mlflow:5000')
else:
    mlflow_tracking_uri = f'file://{os.path.abspath("mlruns")}'
mlflow.set_tracking_uri(mlflow_tracking_uri)

# Obtention du répertoire actuel du fichier
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Charger le modèle
MODEL_PATH = os.getenv('MODEL_PATH', os.path.join(CURRENT_DIR, '..', 'models', 'model.joblib'))
if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")
model = joblib.load(MODEL_PATH)

# Sécurité
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Base de données d'utilisateurs factice
fake_users_db = {
    "student": {
        "username": "student",
        "full_name": "Student User",
        "hashed_password": "fakehashedpassword",
    }
}

def fake_hash_password(password: str):
    return "fakehashed" + password

class User(BaseModel):
    username: str
    full_name: Optional[str] = None  # Utilisez Optional ici

class UserInDB(User):
    hashed_password: str

def authenticate_user(username: str, password: str):
    user = fake_users_db.get(username)
    if not user:
        return False
    if user["hashed_password"] != fake_hash_password(password):
        return False
    return User(**user)

# Fonction pour envoyer des emails d'erreur (désactivée pour le moment)
# def send_error_email(subject: str, message: str):
#     smtp_server = os.getenv("SMTP_SERVER")
#     smtp_port = int(os.getenv("SMTP_PORT", 587))
#     smtp_user = os.getenv("SMTP_USER")
#     smtp_password = os.getenv("SMTP_PASSWORD")
#     recipient = os.getenv("ALERT_EMAIL_RECIPIENT")
#
#     msg = MIMEText(message)
#     msg['Subject'] = subject
#     msg['From'] = smtp_user
#     msg['To'] = recipient
#
#     try:
#         with smtplib.SMTP(smtp_server, smtp_port) as server:
#             server.starttls()
#             server.login(smtp_user, smtp_password)
#             server.send_message(msg)
#         logger.info("Error email sent successfully.")
#     except Exception as e:
#         logger.error(f"Failed to send error email: {e}")

@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Dans une application réelle, retournez un JWT ou un token similaire
    return {"access_token": "fake-token-for-" + user.username, "token_type": "bearer"}

class PredictionRequest(BaseModel):
    features: List[float]

# Métriques Prometheus
REQUEST_COUNT = Counter('request_count', 'Total number of requests')
REQUEST_LATENCY = Histogram('request_latency_seconds', 'Latency of requests in seconds')
PREDICTION_COUNT = Counter('prediction_count', 'Number of predictions made')

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    REQUEST_COUNT.inc()
    with REQUEST_LATENCY.time():
        response = await call_next(request)
    return response

@app.post("/predict")
def predict(request: PredictionRequest, token: str = Depends(oauth2_scheme)):
    try:
        # Vérification d'authentification simplifiée
        if not token.startswith("fake-token-for-"):
            raise HTTPException(status_code=403, detail="Forbidden")

        PREDICTION_COUNT.inc()
        logger.info(f"Received prediction request: {request.features}")

        # Démarrer le chronomètre
        start_time = time.time()

        with mlflow.start_run(run_name="prediction"):
            prediction = model.predict([request.features])

            # Mesurer le temps écoulé
            elapsed_time = time.time() - start_time

            # Extraire le nom d'utilisateur depuis le token
            username = token.replace("fake-token-for-", "")

            # Enregistrer les paramètres et les métriques dans MLflow
            mlflow.log_param("input_features", request.features)
            mlflow.log_param("predicted_value", prediction[0])
            mlflow.log_param("username", username)
            mlflow.log_metric("prediction_time_seconds", elapsed_time)

        logger.info(f"Prediction: {prediction.tolist()}, Time taken: {elapsed_time:.4f} seconds")
        return {"prediction": prediction.tolist(), "prediction_time_seconds": elapsed_time}
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        # Appel à la fonction d'envoi d'email d'erreur (désactivé)
        # send_error_email("API Prediction Error", str(e))
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/model-info")
def model_info(token: str = Depends(oauth2_scheme)):
    try:
        # Vérification d'authentification simplifiée
        if not token.startswith("fake-token-for-"):
            raise HTTPException(status_code=403, detail="Forbidden")

        # Supposons que vous avez un moyen d'obtenir les informations du modèle
        # Pour la démonstration, nous allons retourner des données fictives
        return {
            "model_version": "1.0.0",
            "model_stage": "Production",
            "creation_timestamp": "2024-09-27T13:47:53Z"
        }
    except Exception as e:
        logger.error(f"Error getting model info: {str(e)}")
        # Appel à la fonction d'envoi d'email d'erreur (désactivé)
        # send_error_email("API Model Info Error", str(e))
        raise HTTPException(status_code=500, detail="Error retrieving model information")

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Importer la fonction pour créer la base de données et les tables
from .database import create_db_and_tables

# Initialiser la base de données au démarrage de l'application
@app.on_event("startup")
def on_startup():
    create_db_and_tables()
