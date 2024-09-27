import mlflow
import mlflow.sklearn
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib
import pandas as pd
import yaml  # Importer PyYAML
import os

def load_params(params_path='params.yaml'):
    with open(params_path, 'r') as file:
        params = yaml.safe_load(file)
    return params['train']

def load_data():
    # Chargement des données depuis le fichier CSV versionné par DVC
    data = pd.read_csv('data/raw/iris.csv')
    X = data.drop('species', axis=1)  # Remplacement de 'target' par 'species'
    y = data['species']               # Remplacement de 'target' par 'species'
    return train_test_split(X, y, test_size=0.2, random_state=42)

def train_and_log_model(params_path='params.yaml'):
    params = load_params(params_path)
    X_train, X_test, y_train, y_test = load_data()

    with mlflow.start_run() as run:
        # Entraîner le modèle avec les paramètres chargés
        clf = RandomForestClassifier(
            n_estimators=params['n_estimators'],
            random_state=params['random_state']
        )
        clf.fit(X_train, y_train)

        # Évaluer le modèle
        accuracy = clf.score(X_test, y_test)

        # Enregistrer les métriques et paramètres
        mlflow.log_param("n_estimators", params['n_estimators'])
        mlflow.log_param("random_state", params['random_state'])
        mlflow.log_metric("accuracy", accuracy)

        # Enregistrer le modèle
        mlflow.sklearn.log_model(clf, "model")

        # Sauvegarder le modèle localement
        joblib.dump(clf, '/models/model.joblib')
        print(f"Model trained and logged with run_id: {run.info.run_id}")
        return run.info.run_id

if __name__ == "__main__":
    train_and_log_model()
