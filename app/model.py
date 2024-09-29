# app/model.py

import mlflow
import mlflow.sklearn
from mlflow.tracking import MlflowClient
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib
import pandas as pd
import yaml
import os

def load_params(params_path='params.yaml'):
    with open(params_path, 'r') as file:
        params = yaml.safe_load(file)
    return params['train']

def load_data():
    data = pd.read_csv('data/raw/iris.csv')
    X = data.drop('species', axis=1)
    y = data['species']
    return train_test_split(X, y, test_size=0.2, random_state=42)

def train_and_log_model(params_path='params.yaml'):
    # Détection si on est dans Docker
    if os.environ.get('DOCKER_CONTAINER', False):
        mlflow_tracking_uri = os.getenv('MLFLOW_TRACKING_URI', 'http://mlflow:5000')
    else:
        mlflow_tracking_uri = f'file://{os.path.abspath("mlruns")}'
    mlflow.set_tracking_uri(mlflow_tracking_uri)
    
    params = load_params(params_path)
    X_train, X_test, y_train, y_test = load_data()
    
    # Définir le nom de l'expérience
    experiment_name = "Iris_Classification"
    mlflow.set_experiment(experiment_name)
    
    with mlflow.start_run() as run:
        clf = RandomForestClassifier(
            n_estimators=params['n_estimators'],
            random_state=params['random_state']
        )
        clf.fit(X_train, y_train)
    
        accuracy = clf.score(X_test, y_test)
    
        mlflow.log_param("n_estimators", params['n_estimators'])
        mlflow.log_param("random_state", params['random_state'])
        mlflow.log_metric("accuracy", accuracy)
    
        # Enregistrer le modèle dans MLflow et le registre
        mlflow.sklearn.log_model(
            sk_model=clf,
            artifact_path="model",
            registered_model_name="IrisRandomForestModel"
        )
    
    # Initialiser le client MLflow
    client = MlflowClient()
    
    # Obtenir la dernière version du modèle en production
    try:
        latest_production_versions = client.get_latest_versions(
            name="IrisRandomForestModel", stages=["Production"]
        )
        if latest_production_versions:
            prod_version = latest_production_versions[0]
            prod_run_id = prod_version.run_id
            prod_run = client.get_run(prod_run_id)
            prod_accuracy = prod_run.data.metrics.get("accuracy", 0)
        else:
            prod_accuracy = 0
    except:
        # Pas encore de version en production
        prod_accuracy = 0
    
    # Comparer l'exactitude du nouveau modèle avec celui en production
    if accuracy > prod_accuracy:
        # Obtenir la dernière version du modèle (celle que nous venons d'enregistrer)
        latest_versions = client.get_latest_versions(
            name="IrisRandomForestModel", stages=["None"]
        )
        new_version = latest_versions[0]
        # Promouvoir le nouveau modèle en production
        client.transition_model_version_stage(
            name="IrisRandomForestModel",
            version=new_version.version,
            stage="Production",
            archive_existing_versions=True
        )
        print(f"Nouveau modèle version {new_version.version} promu en Production.")
    else:
        print("Le nouveau modèle n'a pas surpassé le modèle en production ; pas de promotion.")
    
    # Assurer que le répertoire 'models' existe
    os.makedirs('models', exist_ok=True)
    
    # Sauvegarder le modèle localement
    joblib.dump(clf, 'models/model.joblib')
    print(f"Modèle entraîné et enregistré avec run_id: {run.info.run_id}")
    
    return run.info.run_id

if __name__ == "__main__":
    train_and_log_model()
