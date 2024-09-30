from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, conlist, confloat, validator
from typing import List, Optional, Any
import joblib
import os

import logging
import mlflow
from mlflow.tracking import MlflowClient
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response, RedirectResponse  # Import de RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import time

from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

from sqlalchemy.orm import Session

from .database import SessionLocal, create_db_and_tables, get_user, create_user, User as DBUser



app = FastAPI()

@app.get("/")
def redirect_to_docs():
    return RedirectResponse(url="/docs")

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À ajuster en production
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

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def authenticate_user(db, username: str, password: str):
    user = get_user(db, username)
    if not user:
        logger.info(f"Utilisateur '{username}' non trouvé.")
        return None
    if not verify_password(password, user.hashed_password):
        logger.info(f"Mot de passe incorrect pour l'utilisateur '{username}'.")
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)  # Par défaut, expiration dans 15 minutes
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

class Token(BaseModel):
    access_token: str
    token_type: str

class User(BaseModel):
    id: int
    username: str

    class Config:
        orm_mode = True

class UserCreate(BaseModel):
    username: str
    password: str

class PredictionRequest(BaseModel):
    features: conlist(confloat(ge=0, le=50), min_items=4, max_items=4)

    @validator('features')
    def check_features_length(cls, v):
        if len(v) != 4:
            raise ValueError('Le nombre de features doit être exactement 4.')
        return v

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Impossible de valider les informations d'identification",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user(db, username=username)
    if user is None:
        raise credentials_exception
    return user

@app.post("/token", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nom d'utilisateur ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Métriques Prometheus
REQUEST_COUNT = Counter('request_count', 'Nombre total de requêtes')
REQUEST_LATENCY = Histogram('request_latency_seconds', 'Latence des requêtes en secondes')
PREDICTION_COUNT = Counter('prediction_count', 'Nombre de prédictions effectuées')
ERROR_COUNT = Counter('error_count', 'Nombre d\'erreurs')

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    REQUEST_COUNT.inc()
    with REQUEST_LATENCY.time():
        response = await call_next(request)
    return response

@app.post("/predict")
def predict(request: PredictionRequest, current_user: DBUser = Depends(get_current_user)):
    try:
        PREDICTION_COUNT.inc()
        logger.info(f"Requête de prédiction reçue : {request.features}")

        # Set the experiment to "Iris_Classification"
        mlflow.set_experiment("Iris_Classification")

        # Démarrer le chronomètre
        start_time = time.time()

        with mlflow.start_run(run_name="prediction"):
            prediction = model.predict([request.features])

            # Mesurer le temps écoulé
            elapsed_time = time.time() - start_time

            # Enregistrer les paramètres et les métriques dans MLflow
            mlflow.log_param("input_features", request.features)
            mlflow.log_param("predicted_value", prediction[0])
            mlflow.log_param("username", current_user.username)
            mlflow.log_metric("prediction_time_seconds", elapsed_time)

        logger.info(f"Prédiction : {prediction.tolist()}, Temps pris : {elapsed_time:.4f} secondes")
        return {"prediction": prediction.tolist(), "prediction_time_seconds": elapsed_time}
    except Exception as e:
        ERROR_COUNT.inc()
        logger.error(f"Erreur de prédiction : {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")

@app.get("/model-info")
def model_info(current_user: DBUser = Depends(get_current_user)):
    try:
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

# Endpoint pour créer un nouvel utilisateur
@app.post("/users/", response_model=User)
def create_new_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Nom d'utilisateur déjà utilisé")
    hashed_password = get_password_hash(user.password)
    new_user = create_user(db, username=user.username, hashed_password=hashed_password)
    return User.from_orm(new_user)

# Initialiser la base de données au démarrage de l'application
@app.on_event("startup")
def on_startup():
    create_db_and_tables()
