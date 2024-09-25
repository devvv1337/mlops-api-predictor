# Projet MLOps : Classification Iris avec FastAPI, MLflow, DVC, Prometheus, Alertmanager et Grafana

## Table des Matières

- [Description](#description)
- [Architecture du Projet](#architecture-du-projet)
- [Prérequis](#prérequis)
- [Installation](#installation)
- [Configuration](#configuration)
- [Utilisation](#utilisation)
  - [1. Initialiser la Base de Données et Créer un Utilisateur](#1-initialiser-la-base-de-données-et-créer-un-utilisateur)
  - [2. Entraîner le Modèle](#2-entraîner-le-modèle)
  - [3. Accéder à l'API](#3-accéder-à-lapi)
  - [4. Authentification](#4-authentification)
  - [5. Monitoring et Alerting](#5-monitoring-et-alerting)
  - [6. Suivi des Expériences avec MLflow](#6-suivi-des-expériences-avec-mlflow)
- [API Endpoints](#api-endpoints)
- [Tests](#tests)
- [Pipeline CI/CD](#pipeline-cicd)
- [Versionnement des Données avec DVC](#versionnement-des-données-avec-dvc)
- [Déploiement](#déploiement)
- [Bonnes Pratiques MLOps](#bonnes-pratiques-mlops)
- [Difficultés Rencontrées](#difficultés-rencontrées)
- [Points Restants à Réaliser](#points-restants-à-réaliser)
- [Contribution](#contribution)
- [Licence](#licence)

---

## Description

Ce projet implémente un workflow MLOps complet pour un modèle de classification Iris, en utilisant les technologies suivantes :

- **FastAPI** : Fournit une API pour effectuer des prédictions et obtenir des informations sur le modèle.
- **MLflow** : Utilisé pour le suivi des expériences et le versionnement des modèles.
- **DVC (Data Version Control)** : Gère le versionnement des données, avec un stockage distant sur AWS S3.
- **Prometheus** : Collecte les métriques exposées par l'API pour le monitoring.
- **Alertmanager** : Gère les alertes basées sur les métriques collectées.
- **Grafana** : Visualise les métriques collectées via des dashboards personnalisés.
- **Docker & Docker Compose** : Conteneurise l'application et orchestre les services.
- **GitHub Actions** : Implémente un pipeline CI/CD pour automatiser les tests, la construction et le déploiement.
- **Authentification JWT** : Sécurise l'API avec des tokens JWT et des mots de passe hachés de manière sécurisée.

---

## Architecture du Projet

![Architecture Diagram](path/to/architecture_diagram.png)

L'architecture du projet est composée des éléments suivants :

- **API FastAPI** : Conteneur `api`
- **MLflow Server** : Conteneur `mlflow`
- **Prometheus** : Conteneur `prometheus`
- **Alertmanager** : Conteneur `alertmanager`
- **Grafana** : Conteneur `grafana`
- **Stockage Distant S3** : Pour DVC et MLflow
- **Base de Données SQLite** : Pour stocker les utilisateurs de l'API

Tous ces services sont orchestrés via Docker Compose et communiquent entre eux via un réseau Docker dédié.

---

## Prérequis

- **Docker** installé sur votre machine
- **Docker Compose** installé sur votre machine
- **Compte AWS** avec un bucket S3 pour le stockage distant (peut être utilisé avec l'offre gratuite AWS Free Tier)
- **Accès à un serveur SMTP** pour l'envoi d'emails d'alerte (optionnel si vous configurez Alertmanager pour utiliser un autre moyen de notification)
- **Git** pour cloner le dépôt
- **Python 3.9** (si vous souhaitez exécuter le code en dehors des conteneurs Docker)

---

## Installation

1. **Cloner le dépôt :**

   ```bash
   git clone https://github.com/votre-username/mlops_project.git
   cd mlops_project
   ```

2. **Configurer les Variables d'Environnement :**

   Copiez le fichier `.env.example` en `.env` :

   ```bash
   cp .env.example .env
   ```

   Modifiez le fichier `.env` avec vos propres valeurs :

   - `SECRET_KEY` : Clé secrète pour signer les tokens JWT
   - `DATABASE_URL` : URL de connexion à la base de données (par défaut SQLite)
   - `MLFLOW_TRACKING_URI` : URI de tracking de MLflow (par défaut `http://mlflow:5000`)
   - `AWS_ACCESS_KEY_ID` et `AWS_SECRET_ACCESS_KEY` : Vos identifiants AWS
   - `AWS_DEFAULT_REGION` : La région AWS de votre bucket S3

3. **Construire et Lancer les Conteneurs Docker :**

   ```bash
   docker-compose up --build
   ```

   Cela démarre les services suivants :

   - **API FastAPI** : `http://localhost:8000`
   - **Prometheus** : `http://localhost:9090`
   - **Grafana** : `http://localhost:3000`
   - **MLflow** : `http://localhost:5000`
   - **Alertmanager** : `http://localhost:9093`

---

## Configuration

### 1. Configurer Grafana :

- Accédez à `http://localhost:3000` dans votre navigateur.
- Connectez-vous avec les identifiants par défaut :

  - **Utilisateur** : `admin`
  - **Mot de passe** : `admin`

- Changez le mot de passe lors de la première connexion.
- Configurez la source de données Prometheus :

  - Allez dans **Configuration** > **Data Sources**.
  - Ajoutez une nouvelle source de données de type **Prometheus**.
  - Renseignez l'URL : `http://prometheus:9090`
  - Sauvegardez et testez la connexion.

- Importez le dashboard :

  - Allez dans **Create** > **Import**.
  - Cliquez sur **Upload JSON file** et sélectionnez le fichier `dashboards/grafana/dashboards/api_metrics.json`.

### 2. Configurer Alertmanager (Optionnel) :

- Modifiez le fichier `dashboards/alertmanager.yml` pour configurer les notifications selon vos besoins (email, Slack, etc.).
- Si vous utilisez des emails, assurez-vous de configurer les paramètres SMTP.

---

## Utilisation

### 1. Initialiser la Base de Données et Créer un Utilisateur

Par défaut, la base de données SQLite est vide. Vous devez créer un utilisateur pour pouvoir utiliser l'API.

**Étapes :**

1. **Accéder au conteneur API :**

   ```bash
   docker exec -it mlops_api bash
   ```

2. **Lancer le shell Python :**

   ```bash
   python
   ```

3. **Créer un utilisateur :**

   ```python
   from app.database import SessionLocal, User, get_password_hash
   db = SessionLocal()
   new_user = User(username="votre_nom_utilisateur", hashed_password=get_password_hash("votre_mot_de_passe"))
   db.add(new_user)
   db.commit()
   db.close()
   exit()
   ```

4. **Quitter le conteneur :**

   ```bash
   exit
   ```

### 2. Entraîner le Modèle

Vous pouvez entraîner le modèle en exécutant le script `model.py`.

**Étapes :**

```bash
docker exec -it mlops_api python app/model.py
```

Le modèle est entraîné, les métriques et paramètres sont enregistrés dans MLflow, et le modèle est enregistré dans le **Model Registry** de MLflow.

### 3. Accéder à l'API

- **API principale** : `http://localhost:8000`
- **Documentation interactive** : `http://localhost:8000/docs`

### 4. Authentification

L'API est sécurisée avec JWT. Vous devez obtenir un token d'accès pour interagir avec les endpoints protégés.

**Obtenir un token :**

- Envoyez une requête POST à `/token` avec les champs `username` et `password`.

Exemple avec `curl` :

```bash
curl -X POST "http://localhost:8000/token" -d "username=votre_nom_utilisateur&password=votre_mot_de_passe"
```

La réponse contiendra un `access_token` que vous utiliserez dans le header `Authorization` pour les requêtes suivantes :

```bash
Authorization: Bearer votre_access_token
```

### 5. Monitoring et Alerting

- **Prometheus** collecte les métriques exposées par l'API.
- **Grafana** visualise ces métriques via des dashboards personnalisés.
- **Alertmanager** gère les alertes basées sur les règles définies dans `alert.rules.yml`.

**Accéder aux services :**

- **Prometheus** : `http://localhost:9090`
- **Grafana** : `http://localhost:3000`
- **Alertmanager** : `http://localhost:9093`

### 6. Suivi des Expériences avec MLflow

- **MLflow UI** : `http://localhost:5000`

Dans l'interface MLflow, vous pouvez :

- Visualiser les runs d'entraînement du modèle.
- Consulter les métriques et les paramètres enregistrés.
- Gérer les versions du modèle dans le Model Registry.

---

## API Endpoints

### **POST** `/token`

- **Description** : Obtient un token d'accès JWT pour un utilisateur authentifié.
- **Paramètres** :

  - `username` : Nom d'utilisateur.
  - `password` : Mot de passe.

- **Réponse** :

  - `access_token` : Token JWT à utiliser pour les requêtes ultérieures.
  - `token_type` : Type de token (`bearer`).

### **POST** `/predict`

- **Description** : Effectue une prédiction en utilisant le modèle entraîné.
- **Sécurité** : Nécessite un token JWT valide.
- **Corps de la requête** :

  ```json
  {
    "features": [valeur1, valeur2, valeur3, valeur4]
  }
  ```

  - `features` : Liste de 4 valeurs numériques correspondant aux features du dataset Iris.

- **Réponse** :

  ```json
  {
    "prediction": [classe_prévue]
  }
  ```

  - `prediction` : Liste contenant la classe prédite (0, 1 ou 2).

### **GET** `/model-info`

- **Description** : Fournit des informations sur le modèle actuellement déployé.
- **Sécurité** : Nécessite un token JWT valide.
- **Réponse** :

  ```json
  {
    "model_name": "Nom du modèle",
    "model_version": "Version du modèle",
    "current_stage": "Stade actuel (Production, Staging, etc.)",
    "description": "Description du modèle"
  }
  ```

### **GET** `/metrics`

- **Description** : Expose les métriques pour Prometheus.
- **Sécurité** : Pas de sécurité particulière (accessible par Prometheus).

---

## Tests

Les tests unitaires sont implémentés avec `pytest`.

**Exécuter les tests :**

```bash
docker exec -it mlops_api pytest
```

Les tests couvrent :

- L'authentification et l'obtention du token JWT.
- Les endpoints `/predict` et `/model-info`.
- Les cas d'erreur, tels que les données invalides ou les tokens expirés.

---

## Pipeline CI/CD

Le pipeline CI/CD est implémenté avec GitHub Actions et est défini dans `.github/workflows/ci_cd.yml`.

**Fonctionnalités :**

- **Build and Test** : À chaque push ou pull request sur la branche `main`, les tests sont exécutés pour vérifier l'intégrité du code.
- **Docker Build and Push** : Si les tests réussissent, une image Docker est construite et poussée vers Docker Hub.
- **Déploiement** : L'image Docker est déployée sur le serveur de production via SSH.

**Configuration :**

- Les secrets nécessaires (identifiants Docker Hub, clés SSH, etc.) sont stockés en tant que **GitHub Secrets** pour des raisons de sécurité.

---

## Versionnement des Données avec DVC

DVC (Data Version Control) est utilisé pour gérer le versionnement des données.

**Configuration :**

- Le remote est configuré pour utiliser un bucket S3 sur AWS.
- Les identifiants AWS sont gérés via les variables d'environnement dans le fichier `.env`.

**Utilisation :**

- **Ajouter de nouvelles données :**

  ```bash
  dvc add data/raw/nouvelles_donnees.csv
  ```

- **Committer les changements :**

  ```bash
  git add data/raw/nouvelles_donnees.csv.dvc
  git commit -m "Ajout de nouvelles données"
  ```

- **Pousser les données versionnées :**

  ```bash
  dvc push
  ```

- **Tirer les données versionnées :**

  ```bash
  dvc pull
  ```

---

## Déploiement

Le déploiement est géré via Docker Compose.

**Déployer l'application :**

- Sur le serveur cible, assurez-vous que Docker et Docker Compose sont installés.
- Poussez l'image Docker sur un registre (par exemple, Docker Hub).
- Sur le serveur, mettez à jour l'image Docker et relancez les services :

  ```bash
  docker-compose pull
  docker-compose up -d --build
  ```

---

## Bonnes Pratiques MLOps

- **Séparation des Préoccupations** : Chaque composant (API, monitoring, tracking, etc.) est isolé et géré séparément.
- **Automatisation** : Le pipeline CI/CD automatise les tests, la construction et le déploiement.
- **Sécurité** :

  - Les mots de passe sont hachés avec `bcrypt`.
  - L'API est sécurisée avec des tokens JWT signés et expirant.
  - Les secrets (identifiants AWS, clés secrètes) sont gérés via des variables d'environnement et ne sont pas commis dans le contrôle de version.

- **Monitoring et Alerting** : Les métriques critiques sont surveillées, et des alertes sont envoyées en cas de problème.
- **Scalabilité** : L'application peut être déployée sur un orchestrateur de conteneurs comme Kubernetes pour une scalabilité horizontale.

---

## Difficultés Rencontrées

- **Gestion des Dépendances** : Assurer la compatibilité entre les versions des bibliothèques et des services.
- **Sécurisation de l'API** : Implémenter une authentification robuste tout en maintenant la simplicité d'utilisation.
- **Configuration des Outils de Monitoring** : Harmoniser les configurations entre Prometheus, Alertmanager et Grafana.

---

## Points Restants à Réaliser

- **Déploiement sur Kubernetes** : Pour une scalabilité et une résilience accrues.
- **Tests de Charge et de Performance** : Pour évaluer le comportement de l'application sous une forte charge.
- **Gestion des Secrets Plus Sécurisée** : Utiliser un gestionnaire de secrets dédié (comme HashiCorp Vault).
- **Amélioration de la Couverture des Tests** : Ajouter des tests de bout en bout et des tests d'intégration.

---




