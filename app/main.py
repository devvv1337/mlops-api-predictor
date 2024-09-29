from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Optional
import joblib
import os
from dotenv import load_dotenv

import logging
import mlflow
from mlflow.tracking import MlflowClient
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
import time

load_dotenv()

app = FastAPI()

# Middleware CORS (optionnel, ajustez selon vos besoins)
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

# Initialiser le client MLflow
client = MlflowClient()

# Obtenir le modèle en production le plus récent
def load_production_model():
    try:
        latest_production_versions = client.get_latest_versions(
            name="IrisRandomForestModel", stages=["Production"]
        )
        if latest_production_versions:
            prod_version = latest_production_versions[0]
            model_uri = f"models:/{prod_version.name}/{prod_version.version}"
            model = mlflow.pyfunc.load_model(model_uri)
            logger.info(f"Chargé le modèle version {prod_version.version} depuis le stage Production.")
            return model
        else:
            raise Exception("Aucun modèle en stage Production.")
    except Exception as e:
        logger.error(f"Échec du chargement du modèle depuis le registre MLflow : {e}")
        raise

try:
    model = load_production_model()
except Exception as e:
    # Repli sur le modèle local si disponible
    logger.warning("Repli sur le modèle local.")
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    MODEL_PATH = os.getenv('MODEL_PATH', os.path.join(CURRENT_DIR, '..', 'models', 'model.joblib'))
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Fichier modèle introuvable à {MODEL_PATH}")
    model = joblib.load(MODEL_PATH)
    logger.info("Modèle local chargé.")

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
    full_name: Optional[str] = None

class UserInDB(User):
    hashed_password: str

def authenticate_user(username: str, password: str):
    user = fake_users_db.get(username)
    if not user:
        return False
    if user["hashed_password"] != fake_hash_password(password):
        return False
    return User(**user)

@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nom d'utilisateur ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Dans une application réelle, retournez un JWT ou un token similaire
    return {"access_token": "fake-token-for-" + user.username, "token_type": "bearer"}

class PredictionRequest(BaseModel):
    features: List[float]

# Métriques Prometheus
REQUEST_COUNT = Counter('request_count', 'Nombre total de requêtes')
REQUEST_LATENCY = Histogram('request_latency_seconds', 'Latence des requêtes en secondes')
PREDICTION_COUNT = Counter('prediction_count', 'Nombre de prédictions effectuées')

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
            raise HTTPException(status_code=403, detail="Accès refusé")

        PREDICTION_COUNT.inc()
        logger.info(f"Requête de prédiction reçue : {request.features}")

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

        logger.info(f"Prédiction : {prediction.tolist()}, Temps pris : {elapsed_time:.4f} secondes")
        return {"prediction": prediction.tolist(), "prediction_time_seconds": elapsed_time}
    except Exception as e:
        logger.error(f"Erreur de prédiction : {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")

@app.get("/model-info")
def model_info(token: str = Depends(oauth2_scheme)):
    try:
        # Vérification d'authentification simplifiée
        if not token.startswith("fake-token-for-"):
            raise HTTPException(status_code=403, detail="Accès refusé")

        # Obtenir les informations du modèle depuis le registre MLflow
        latest_production_versions = client.get_latest_versions(
            name="IrisRandomForestModel", stages=["Production"]
        )
        if latest_production_versions:
            prod_version = latest_production_versions[0]
            return {
                "model_name": prod_version.name,
                "model_version": prod_version.version,
                "current_stage": prod_version.current_stage,
                "description": prod_version.description,
                "creation_timestamp": prod_version.creation_timestamp,
                "last_updated_timestamp": prod_version.last_updated_timestamp,
                "run_id": prod_version.run_id,
            }
        else:
            raise Exception("Aucun modèle en stage Production.")
    except Exception as e:
        logger.error(f"Erreur lors de l'obtention des informations du modèle : {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des informations du modèle")

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Importer la fonction pour créer la base de données et les tables
from .database import create_db_and_tables

# Initialiser la base de données au démarrage de l'application
@app.on_event("startup")
def on_startup():
    create_db_and_tables()
