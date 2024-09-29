# MLOps API Predictor

Ce projet implémente une API prédictive basée sur FastAPI, avec un pipeline d'entraînement de modèle utilisant **MLflow** et **DVC**. Le projet est orchestré via **Docker** et inclut des dashboards de monitoring avec **Prometheus** et **Grafana**.

## Prérequis

- Docker et Docker Compose
- AWS S3 (pour le stockage de modèle via DVC)
- Python 3.9+ (si exécuté en local)

## Installation et configuration

1. **Cloner le dépôt :**

   ```bash
   git clone https://github.com/mlops-api-predictor.git
   cd mlops-api-predictor
   ```

2. **Configurer les variables d'environnement :**

   Copier le fichier `.env.example` et le renommer en `.env`. Remplissez les valeurs manquantes (ex: clés AWS, secret keys) :

   ```bash
   cp .env.example .env
   ```

3. **Lancer le projet avec Docker Compose :**

   ```bash
   docker-compose up --build
   ```

   Cela démarre les services suivants :
   - **trainer** : Entraîne le modèle et le log dans MLflow.
   - **api** : API FastAPI pour les prédictions.
   - **prometheus** : Monitoring des métriques.
   - **grafana** : Visualisation des métriques.
   - **mlflow** : Serveur MLflow pour suivre les expériences.
   - **alertmanager** : Gestion des alertes pour Prometheus.

## URL des services

- **API FastAPI** : [http://localhost:8000](http://localhost:8000)
  - Endpoints :
    - `/predict` : Prédiction à partir des caractéristiques.
    - `/metrics` : Métriques Prometheus.
    - `/model-info` : Informations sur le modèle.
    - `/token` : Obtenir un token d'accès.
  
- **MLflow UI** : [http://localhost:5000](http://localhost:5000)
- **Prometheus** : [http://localhost:9090](http://localhost:9090)
- **Grafana** : [http://localhost:3000](http://localhost:3000) (user: `admin`, password: `admin`)

## Architecture du projet

- **app/** : Code source de l'application.
  - `main.py` : API FastAPI pour prédictions.
  - `model.py` : Pipeline d'entraînement du modèle avec MLflow.
  - `database.py` : Gestion de la base de données (utilisateurs).
  - `entrypoint.sh` : Script d'initialisation du conteneur Docker.
- **dashboards/** : Configuration pour Prometheus, Grafana et les règles d'alertes.
- **models/** : Dossier où le modèle est sauvegardé après l'entraînement.
- **data/** : Données pour l'entraînement du modèle.
- **tests/** : Tests unitaires et d'intégration.

## Entraînement du modèle

Le modèle est entraîné automatiquement lors de l'exécution du service **trainer**. Vous pouvez aussi l'entraîner manuellement en lançant la commande :

```bash
docker-compose run trainer
```

Le modèle est enregistré dans `models/model.joblib` et les expériences sont traquées dans **MLflow**.

## Intégration AWS et Pratiques MLOps

### Gestion du versioning des modèles

Le projet utilise **DVC (Data Version Control)** pour la gestion des versions des modèles et des données, avec **AWS S3** comme stockage distant. Voici comment cela fonctionne :

1. **DVC pour le suivi des modèles** :
   - Après chaque entraînement, le modèle est sauvegardé localement dans le répertoire `models/` et versionné avec DVC.
   - **Remarque** : Les modèles ne sont pas automatiquement **poussés** sur AWS S3 après chaque entraînement. Vous devez **pousser manuellement** le modèle sur S3 avec la commande suivante :
   
     ```bash
     dvc push models/model.joblib
     ```

2. **Configuration S3 dans DVC** :
   Le fichier `.env` spécifie les **credentials AWS** nécessaires pour interagir avec le bucket S3 :

   ```env
   AWS_ACCESS_KEY_ID=your_access_key_id
   AWS_SECRET_ACCESS_KEY=your_secret_access_key
   AWS_DEFAULT_REGION=eu-north-1
   ```

   Dans **DVC**, les versions des modèles et des données sont gérées via des **hashes** de fichiers (voir `dvc.lock` et `params.yaml`), permettant de reproduire n'importe quelle version d'un modèle avec ses paramètres spécifiques.

### Suivi des expériences avec MLflow

Le projet utilise **MLflow** pour suivre les expérimentations et les métriques de performance des modèles. Chaque fois que vous exécutez l'entraînement :

- Les **paramètres d'entraînement** (par exemple, `n_estimators`, `random_state`) sont enregistrés dans **MLflow**.
- Les **métriques de performance** (précision du modèle, latence des prédictions) sont également traquées.
- Les modèles sont **loggés** dans MLflow, permettant de les charger ultérieurement pour des tests ou des déploiements.

MLflow expose une interface web à [http://localhost:5000](http://localhost:5000), où vous pouvez consulter toutes les expérimentations passées.

### Monitoring et alertes avec Prometheus et Grafana

Nous avons implémenté une surveillance active de l'API via **Prometheus** pour collecter des métriques telles que :
- Le **nombre de requêtes** reçues par l'API.
- La **latence** des requêtes.
- Le **nombre de prédictions** effectuées.

Ces métriques sont visualisées via **Grafana** à [http://localhost:3000](http://localhost:3000), avec des dashboards prédéfinis dans `dashboards/grafana`. **Prometheus Alertmanager** est configuré pour générer des **alertes** en cas d'anomalies, telles qu'un taux d'erreur élevé.

### Bonnes pratiques MLOps implémentées

1. **Versioning des modèles et des données** :
   - **DVC** gère la version des données et des modèles, garantissant une traçabilité complète des fichiers et des modèles.
   
2. **Suivi des expérimentations** :
   - **MLflow** suit toutes les expérimentations, enregistre les hyperparamètres, métriques, et modèles.

3. **Continuous Integration (CI)** :
   - Des **tests unitaires** et d'**intégration** sont en place pour vérifier la qualité du modèle (`tests/`), garantissant que chaque version est testée avant déploiement.

4. **Déploiement containerisé** :
   - **Docker** est utilisé pour garantir la **portabilité** du projet, permettant un déploiement uniforme sur n'importe quelle machine ou cloud.

5. **Surveillance et alertes** :
   - Les métriques de l'API sont surveillées en temps réel grâce à **Prometheus** et visualisées avec **Grafana**, avec des alertes automatiques en cas de problème.

