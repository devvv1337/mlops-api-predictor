from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List
import joblib
import os
from dotenv import load_dotenv
import logging
import mlflow
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
import smtplib
from email.mime.text import MIMEText

load_dotenv()

app = FastAPI()

# CORS Middleware (optional, adjust as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load Model
MODEL_PATH = 'models/model.joblib'
model = joblib.load(MODEL_PATH)

# Security
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Dummy user database
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
    full_name: str | None = None

class UserInDB(User):
    hashed_password: str

def authenticate_user(username: str, password: str):
    user = fake_users_db.get(username)
    if not user:
        return False
    if user["hashed_password"] != fake_hash_password(password):
        return False
    return User(**user)

def send_error_email(subject: str, message: str):
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    recipient = os.getenv("ALERT_EMAIL_RECIPIENT")

    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = smtp_user
    msg['To'] = recipient

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        logger.info("Error email sent successfully.")
    except Exception as e:
        logger.error(f"Failed to send error email: {e}")

@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # In a real application, return a JWT or similar token
    return {"access_token": "fake-token-for-" + user.username, "token_type": "bearer"}

class PredictionRequest(BaseModel):
    features: List[float]

# Prometheus Metrics
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
        # Authentication placeholder
        if not token.startswith("fake-token-for-"):
            raise HTTPException(status_code=403, detail="Forbidden")
        
        PREDICTION_COUNT.inc()
        logger.info(f"Received prediction request: {request.features}")
        with mlflow.start_run(run_name="prediction"):
            prediction = model.predict([request.features])
            mlflow.log_param("input_features", request.features)
            mlflow.log_metric("prediction", prediction[0])
        logger.info(f"Prediction: {prediction.tolist()}")
        return {"prediction": prediction.tolist()}
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        send_error_email("API Prediction Error", str(e))
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/model-info")
def model_info(token: str = Depends(oauth2_scheme)):
    try:
        # Authentication placeholder
        if not token.startswith("fake-token-for-"):
            raise HTTPException(status_code=403, detail="Forbidden")
        
        model_info = mlflow.sklearn.get_model_info("models/model.joblib")
        return {
            "model_version": model_info.version,
            "model_stage": model_info.stage,
            "creation_timestamp": model_info.creation_timestamp
        }
    except Exception as e:
        logger.error(f"Error getting model info: {str(e)}")
        send_error_email("API Model Info Error", str(e))
        raise HTTPException(status_code=500, detail="Error retrieving model information")

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
