import joblib
import numpy as np
from app.model import train_and_log_model, load_data
import mlflow
import os

def test_model_training():
    os.environ["MLFLOW_TRACKING_URI"] = "http://localhost:5000"
    run_id = train_and_log_model()
    assert run_id is not None

    model = joblib.load('models/model.joblib')
    assert model is not None

    client = mlflow.tracking.MlflowClient()
    run = client.get_run(run_id)
    assert run.data.metrics["accuracy"] > 0.8

def test_model_prediction():
    model = joblib.load('models/model.joblib')
    X_train, X_test, _, _ = load_data()
    sample_input = X_test.iloc[0].values.reshape(1, -1)
    prediction = model.predict(sample_input)
    assert prediction.shape == (1,)
    assert prediction[0] in [0, 1, 2]  # Iris dataset has 3 classes

def test_data_versioning():
    X_train, X_test, y_train, y_test = load_data()
    assert len(X_train) + len(X_test) == 150  # Total number of samples in Iris dataset
    assert X_train.shape[1] == 4  # Number of features
