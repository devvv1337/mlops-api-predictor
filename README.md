# Guide Complet pour Déployer l'Application MLOps avec Docker

Bienvenue dans ce projet MLOps qui intègre un pipeline complet de Machine Learning avec FastAPI, MLflow, DVC, Prometheus, Grafana et Docker. Ce guide vous fournira des instructions détaillées pour configurer, déployer et utiliser l'application en vous concentrant sur la partie Docker.

## Table des Matières

- [Aperçu du Projet](#aperçu-du-projet)
- [Architecture](#architecture)
- [Prérequis](#prérequis)
- [Configuration du Projet](#configuration-du-projet)
  - [1. Cloner le Référentiel](#1-cloner-le-référentiel)
  - [2. Configurer les Variables d'Environnement](#2-configurer-les-variables-denvironnement)
  - [3. Configurer DVC pour le Versionnement des Données](#3-configurer-dvc-pour-le-versionnement-des-données)
  - [4. Configurer MLflow pour le Suivi des Expériences](#4-configurer-mlflow-pour-le-suivi-des-expériences)
- [Déploiement avec Docker](#déploiement-avec-docker)
  - [1. Construire les Images Docker](#1-construire-les-images-docker)
  - [2. Démarrer les Services avec Docker Compose](#2-démarrer-les-services-avec-docker-compose)
  - [3. Vérifier le Déploiement](#3-vérifier-le-déploiement)
- [Utilisation de l'API](#utilisation-de-lapi)
  - [1. Obtenir un Token d'Authentification](#1-obtenir-un-token-dauthentification)
  - [2. Effectuer une Prédiction](#2-effectuer-une-prédiction)
  - [3. Consulter les Informations du Modèle](#3-consulter-les-informations-du-modèle)
- [Surveillance et Alertes](#surveillance-et-alertes)
  - [1. Accéder à Prometheus](#1-accéder-à-prometheus)
  - [2. Accéder à Grafana](#2-accéder-à-grafana)
  - [3. Configurer Alertmanager](#3-configurer-alertmanager)
- [Tests](#tests)

---

## Aperçu du Projet

Ce projet est une application de classification d'iris qui utilise un modèle de Machine Learning entraîné avec Scikit-learn. L'application expose une API RESTful construite avec FastAPI pour effectuer des prédictions en temps réel. Elle intègre également des outils MLOps tels que MLflow pour le suivi des expériences, DVC pour le versionnement des données, et des solutions de surveillance avec Prometheus et Grafana. Le déploiement est entièrement géré via Docker pour faciliter la configuration et l'orchestration des services.

## Architecture

L'architecture du projet se compose des composants suivants, tous orchestrés via Docker :

- **API FastAPI** : Fournit l'API pour les prédictions et les informations du modèle.
- **Service d'Entraînement** : Entraîne le modèle et l'enregistre.
- **MLflow** : Utilisé pour le suivi des expériences et le stockage des artefacts du modèle.
- **DVC** : Gère le versionnement des données.
- **Prometheus** : Collecte les métriques pour la surveillance.
- **Grafana** : Visualise les métriques collectées.
- **Alertmanager** : Gère les alertes basées sur les règles définies.
- **Docker Compose** : Orchestre tous les services dans des conteneurs Docker.

## Prérequis

Assurez-vous que les outils suivants sont installés sur votre système :

- **Git** : Pour cloner le référentiel.
- **Docker** : Pour le déploiement des conteneurs.
- **Docker Compose** : Pour orchestrer les services Docker.

## Configuration du Projet

### 1. Cloner le Référentiel

Commencez par cloner le référentiel Git sur votre machine locale :

```bash
git clone https://github.com/votre-utilisateur/votre-repo.git
cd votre-repo
```

### 2. Configurer les Variables d'Environnement

Le projet utilise un fichier `.env` pour gérer les variables d'environnement nécessaires à la configuration des services. Suivez les étapes ci-dessous pour configurer vos variables d'environnement :

1. **Copiez le fichier d'exemple** `.env.example` pour créer votre propre fichier `.env` :

   ```bash
   cp .env.example .env
   ```

2. **Modifiez le fichier `.env`** pour y ajouter vos propres configurations :

   - **SECRET_KEY** : Une clé secrète pour sécuriser l'API. Vous pouvez générer une clé en utilisant la commande suivante en Python :

     ```python
     import secrets
     print(secrets.token_urlsafe(32))
     ```

   - **DATABASE_URL** : L'URL de connexion à la base de données. Par défaut, une base de données SQLite est utilisée.

   - **MLFLOW_TRACKING_URI** : L'URI pour le suivi MLflow. Dans le contexte de Docker, utilisez `http://mlflow:5000`.

   - **AWS Credentials** : Si vous utilisez AWS pour le stockage des données ou des artefacts, ajoutez vos identifiants AWS. **Ne partagez jamais vos clés AWS dans un référentiel public.**

   Exemple de fichier `.env` :

   ```env
   # API Configuration
   SECRET_KEY=your_generated_secret_key

   # Database URL
   DATABASE_URL=sqlite:///./users.db

   # MLflow Tracking URI
   MLFLOW_TRACKING_URI=http://mlflow:5000

   # AWS Credentials (si nécessaire)
   AWS_ACCESS_KEY_ID=your_access_key_id
   AWS_SECRET_ACCESS_KEY=your_secret_access_key
   AWS_DEFAULT_REGION=us-east-1
   ```

### 3. Configurer DVC pour le Versionnement des Données

Le projet utilise DVC pour gérer le versionnement des données. Assurez-vous que DVC est correctement configuré :

1. **Installer DVC** (si ce n'est pas déjà fait) :

   ```bash
   pip install dvc
   ```

2. **Configurer le Remote DVC** : Si vous utilisez un stockage distant pour les données (par exemple, AWS S3), configurez-le en utilisant :

   ```bash
   dvc remote add -d myremote s3://mybucket/path
   ```

3. **Récupérer les Données** :

   ```bash
   dvc pull
   ```

### 4. Configurer MLflow pour le Suivi des Expériences

MLflow est utilisé pour le suivi des expériences et le stockage des artefacts du modèle.

- **Assurez-vous que le fichier `mlflow.yaml`** est correctement configuré :

  ```yaml
  artifact_location: ./mlruns
  experiment_name: iris_classification
  ```

- **Note** : Dans le contexte de Docker, MLflow est déployé comme un service Docker séparé et accessible via `http://mlflow:5000`.

## Déploiement avec Docker

Le déploiement de l'application est orchestré via Docker Compose, ce qui facilite le lancement de tous les services nécessaires.

### 1. Construire les Images Docker

Avant de démarrer les services, vous devez construire les images Docker pour l'API et le service d'entraînement :

```bash
docker-compose build
```

Cette commande lit le `Dockerfile` et crée les images Docker nécessaires.

### 2. Démarrer les Services avec Docker Compose

Lancez tous les services définis dans `docker-compose.yml` en mode détaché :

```bash
docker-compose up -d
```

Les services suivants seront démarrés :

- **trainer** : Entraîne le modèle et le stocke.
- **api** : Expose l'API FastAPI pour les prédictions.
- **mlflow** : Service MLflow pour le suivi des expériences.
- **prometheus** : Collecte les métriques pour la surveillance.
- **grafana** : Visualise les métriques collectées.
- **alertmanager** : Gère les alertes basées sur les règles définies.

### 3. Vérifier le Déploiement

Vous pouvez vérifier que les conteneurs sont en cours d'exécution en utilisant :

```bash
docker-compose ps
```

Assurez-vous que tous les services sont `Up`.

## Utilisation de l'API

Une fois que tous les services sont démarrés, vous pouvez interagir avec l'API pour effectuer des prédictions.

### 1. Obtenir un Token d'Authentification

L'API utilise OAuth2 pour l'authentification. Pour obtenir un token, effectuez une requête POST :

```bash
curl -X POST "http://localhost:8000/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=student&password=yourpassword"
```

**Remarque** : Par défaut, un utilisateur fictif `student` est configuré avec le mot de passe `fakehashedpassword`. Vous pouvez modifier les utilisateurs dans le fichier `./app/main.py` ou configurer une base de données réelle.

### 2. Effectuer une Prédiction

Utilisez le token obtenu pour effectuer une prédiction :

```bash
curl -X POST "http://localhost:8000/predict" \
     -H "Authorization: Bearer votre_token" \
     -H "Content-Type: application/json" \
     -d '{"features": [5.1, 3.5, 1.4, 0.2]}'
```

Vous devriez recevoir une réponse JSON avec la prédiction du modèle.

### 3. Consulter les Informations du Modèle

Vous pouvez également obtenir des informations sur le modèle déployé :

```bash
curl -X GET "http://localhost:8000/model-info" \
     -H "Authorization: Bearer votre_token"
```

## Surveillance et Alertes

Le projet intègre Prometheus et Grafana pour la surveillance, ainsi qu'Alertmanager pour la gestion des alertes.

### 1. Accéder à Prometheus

Prometheus collecte les métriques exposées par l'API. Vous pouvez accéder à l'interface de Prometheus via :

- **URL** : `http://localhost:9090`

Vous pouvez utiliser l'interface pour exécuter des requêtes PromQL et visualiser les métriques collectées.

### 2. Accéder à Grafana

Grafana est utilisé pour visualiser les métriques collectées par Prometheus.

- **URL** : `http://localhost:3000`
- **Identifiants par défaut** :
  - **Utilisateur** : `admin`
  - **Mot de passe** : `admin`

#### Importer le Dashboard

Pour visualiser les métriques de l'API, importez le dashboard fourni :

1. Connectez-vous à Grafana.
2. Cliquez sur le bouton **"+"** dans la barre latérale gauche et sélectionnez **"Import"**.
3. Cliquez sur **"Upload .json File"** et sélectionnez le fichier `dashboards/grafana/dashboards/api_metrics.json`.
4. Cliquez sur **"Import"**.

### 3. Configurer Alertmanager

Alertmanager gère les alertes basées sur les règles définies dans `dashboards/alert.rules.yml`. Par défaut, les alertes sont configurées pour être envoyées par email.

#### Configurer les Paramètres SMTP

Modifiez le fichier `dashboards/alertmanager.yml` pour configurer vos paramètres SMTP :

```yaml
global:
  resolve_timeout: 5m

route:
  receiver: 'email-notifications'

receivers:
  - name: 'email-notifications'
    email_configs:
      - to: 'alerts@example.com'
        from: 'alertmanager@example.com'
        smarthost: 'smtp.example.com:587'
        auth_username: 'smtp_user'
        auth_password: 'smtp_password'
```

**Remarque** : Remplacez les valeurs par vos propres informations.

#### Redémarrer Alertmanager

Après avoir modifié la configuration, redémarrez le conteneur Alertmanager :

```bash
docker-compose restart alertmanager
```

## Tests

Le projet inclut des tests pour vérifier le bon fonctionnement du modèle et de l'API.

### Exécuter les Tests

Vous pouvez exécuter les tests en utilisant Docker :

```bash
docker-compose run --rm api pytest tests/
```

Cela exécutera les tests définis dans le dossier `tests/` à l'intérieur du conteneur `api`.

---

**Remarque** : N'oubliez pas de sécuriser vos informations sensibles et de ne jamais les partager publiquement. Assurez-vous également de respecter les politiques de sécurité de votre organisation lors de l'utilisation de ce projet.