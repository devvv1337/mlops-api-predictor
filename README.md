# MLOps API Predictor

Welcome to the **MLOps API Predictor** project! This application provides a robust framework for training, deploying, and managing machine learning models using modern MLOps practices. Leveraging Docker, MLflow, Prometheus, Grafana, and AWS, this project ensures seamless integration, monitoring, and scalability for your machine learning workflows.

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running the Application](#running-the-application)
- [Services and Endpoints](#services-and-endpoints)
- [AWS Integration](#aws-integration)
- [Project Workflow](#project-workflow)
- [Testing](#testing)
- [Monitoring and Alerts](#monitoring-and-alerts)


## Features

- **User Authentication**: Secure user authentication using OAuth2 with JWT tokens.
- **Model Training and Logging**: Train machine learning models with automatic logging of parameters and metrics using MLflow.
- **Model Versioning and Promotion**: Manage multiple versions of models and promote the best-performing model to production.
- **API for Predictions**: RESTful API endpoints for making predictions with the deployed model.
- **Metrics Collection**: Monitor API performance and model predictions using Prometheus.
- **Dashboard Visualization**: Visualize metrics and system health using Grafana.
- **Alerting System**: Receive alerts on critical metrics via Alertmanager.
- **AWS Integration**: Store MLflow artifacts in AWS S3 for scalability and reliability.
- **Ngrok Integration**: Expose the API securely to the internet for testing and demonstration purposes.

## Architecture

The project is structured using a microservices architecture, orchestrated by Docker Compose. Below is an overview of the main components:

![Architecture Diagram](https://i.imgur.com/fMkL7Vp.png)


### Components

- **API Service**: FastAPI-based service that handles user authentication, predictions, and serves the API endpoints.
- **Trainer Service**: Handles model training, logging, and versioning using MLflow.
- **MLflow Server**: Manages experiment tracking and model registry, storing artifacts in AWS S3.
- **Prometheus**: Collects and stores metrics from the API service.
- **Grafana**: Visualizes metrics from Prometheus through customizable dashboards.
- **Alertmanager**: Manages alerts triggered by Prometheus based on predefined rules.
- **Grafana**: Visualizes metrics from Prometheus through customizable dashboards.
- **Ngrok**: Provides secure tunnels to expose the API service to the internet.

## Prerequisites

Before you begin, ensure you have met the following requirements:

- **Docker**: Installed on your machine. [Download Docker](https://www.docker.com/get-started)
- **Docker Compose**: Installed alongside Docker.
- **AWS Account**: For S3 storage and credentials.
- **Ngrok Account**: For exposing the API to the internet.

## Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourusername/mlops-api-predictor.git
   cd mlops-api-predictor
   ```

2. **Create Environment Variables**

   - Duplicate the `.env.example` file and rename it to `.env`.

     ```bash
     cp .env.example .env
     ```

   - Populate the `.env` file with your specific configurations:

     - **API Configuration**: Set a strong `SECRET_KEY`.
     - **Database URL**: By default, it uses SQLite. Adjust if needed.
     - **AWS Credentials**: Enter your `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION`, and `AWS_S3_BUCKET`.
     - **Ngrok Configuration**: Add your `NGROK_AUTHTOKEN`.

     ```env
     # API Configuration
     SECRET_KEY=your_secret_key_here

     # Database URL
     DATABASE_URL=sqlite:///./users.db

     # MLflow Tracking URI
     MLFLOW_TRACKING_URI=http://mlflow:5000 

     # AWS Credentials (replace with your own keys)
     AWS_ACCESS_KEY_ID=your_aws_access_key_here
     AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key_here
     AWS_DEFAULT_REGION=eu-north-1
     AWS_S3_BUCKET=your_s3_bucket_here

     # MLflow Artifact Root
     MLFLOW_ARTIFACT_ROOT=s3://${AWS_S3_BUCKET}/mlartifacts

     # ngrok Configuration
     NGROK_AUTHTOKEN=your_ngrok_authtoken_here
     ```

3. **Build and Start Services**

   Use Docker Compose to build and run all the services.

   ```bash
   docker-compose up --build
   ```

   This command will:

   - Build Docker images for the API and Trainer services.
   - Pull necessary Docker images for Prometheus, Grafana, Alertmanager, MLflow, and Ngrok.
   - Start all services and ensure they are networked correctly.

## Running the Application

1. **Initialize the Database and Train the Model**

   The `trainer` service automatically initializes the database and trains the model upon starting.

2. **Accessing the Services**

   - **API Service**: Accessible at [http://localhost:8000](http://localhost:8000)
   - **MLflow UI**: Accessible at [http://localhost:5000](http://localhost:5000)
   - **Prometheus**: Accessible at [http://localhost:9090](http://localhost:9090)
   - **Grafana**: Accessible at [http://localhost:3000](http://localhost:3000) (default credentials: `admin/admin`)
   - **Alertmanager**: Accessible at [http://localhost:9093](http://localhost:9093)
   - **Ngrok Dashboard**: Accessible at [http://localhost:4040](http://localhost:4040)

3. **Expose API via Ngrok**

   Ngrok is configured to expose the API service to the internet. After running `docker-compose up`, Ngrok will provide a public URL accessible from anywhere.

   - Find the public URL in the Ngrok dashboard at [http://localhost:4040](http://localhost:4040).
   - Use this URL to make API requests externally.

## Services and Endpoints

### API Service

- **Base URL**: `http://localhost:8000` or your Ngrok URL.

#### Authentication

- **Login**

  - **Endpoint**: `/token`
  - **Method**: `POST`
  - **Description**: Authenticate user and retrieve JWT token.
  - **Parameters**:
    - `username`: String
    - `password`: String

- **Create User**

  - **Endpoint**: `/users/`
  - **Method**: `POST`
  - **Description**: Register a new user.
  - **Body**:
    ```json
    {
      "username": "your_username",
      "password": "your_password"
    }
    ```

#### Prediction

- **Make Prediction**

  - **Endpoint**: `/predict`
  - **Method**: `POST`
  - **Description**: Get a prediction from the deployed model.
  - **Headers**:
    - `Authorization`: `Bearer <JWT_TOKEN>`
  - **Body**:
    ```json
    {
      "features": [5.1, 3.5, 1.4, 0.2]
    }
    ```

- **Model Information**

  - **Endpoint**: `/model-info`
  - **Method**: `GET`
  - **Description**: Retrieve information about the current production model.
  - **Headers**:
    - `Authorization`: `Bearer <JWT_TOKEN>`

#### Metrics

- **Prometheus Metrics**

  - **Endpoint**: `/metrics`
  - **Method**: `GET`
  - **Description**: Expose Prometheus-compatible metrics.

### MLflow

- **MLflow UI**

  - **URL**: `http://localhost:5000`
  - **Description**: Monitor experiments, runs, and models.

### Prometheus

- **Prometheus UI**

  - **URL**: `http://localhost:9090`
  - **Description**: Explore and query metrics.

### Grafana

- **Grafana UI**

  - **URL**: `http://localhost:3000`
  - **Description**: Visualize metrics with customizable dashboards.
  - **Default Credentials**:
    - **Username**: `admin`
    - **Password**: `admin`

### Alertmanager

- **Alertmanager UI**

  - **URL**: `http://localhost:9093`
  - **Description**: Manage alerts and notification channels.

### Ngrok

- **Ngrok Dashboard**

  - **URL**: `http://localhost:4040`
  - **Description**: Monitor Ngrok tunnels and access logs.

## AWS Integration

This project leverages AWS S3 for storing MLflow artifacts, ensuring scalability and reliability.

### Configuration

- **AWS Credentials**: Set in the `.env` file (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`).
- **S3 Bucket**: Specify your S3 bucket name in `AWS_S3_BUCKET` within the `.env` file.
- **Artifact Storage**: MLflow is configured to use S3 as the artifact root (`MLFLOW_ARTIFACT_ROOT`).

### Usage

- **Storing Artifacts**: All MLflow artifacts, including models and logs, are stored in the specified S3 bucket.
- **Model Retrieval**: During prediction, models are pulled from S3 via MLflow's artifact store.

## Project Workflow

The following steps outline the workflow from starting the application to deploying a new model:

1. **Start Services**

   ```bash
   docker-compose up --build
   ```

2. **Initialize Database and Train Model**

   - The `trainer` service initializes the SQLite database and trains the initial model.
   - Trained models are logged to MLflow and stored in S3.

3. **Model Evaluation and Promotion**

   - After training, the system evaluates the new model's accuracy against the current production model.
   - If the new model performs better, it is automatically promoted to the production stage in MLflow.

4. **API Deployment**

   - The `api` service loads the production model from MLflow.
   - Exposes endpoints for making predictions and retrieving model information.

5. **Monitoring and Alerts**

   - Prometheus scrapes metrics from the API service.
   - Grafana visualizes these metrics for real-time monitoring.
   - Alertmanager sends notifications based on predefined alert rules.

6. **External Access via Ngrok**

   - Ngrok exposes the API service to the internet.
   - Useful for testing, demonstrations, or integrations with external systems.

7. **Continuous Integration and Deployment**

   - Use the provided `tests/` directory to run unit and integration tests.
   - Implement CI/CD pipelines to automate testing and deployment.

## Testing

Ensure the application is functioning correctly by running the provided tests.

1. **Run Unit and Integration Tests**

   ```bash
   docker-compose exec api pytest
   ```

   This command executes all tests located in the `tests/` directory.

2. **Test Coverage**

   The project includes coverage reporting to ensure code quality.

   ```bash
   docker-compose exec api pytest --cov=app
   ```

## Monitoring and Alerts

The application includes comprehensive monitoring and alerting to ensure reliability and performance.

### Prometheus

- **Metrics Collected**:
  - Total number of requests (`request_count`)
  - Request latency (`request_latency_seconds`)
  - Number of predictions (`prediction_count`)
  - Error count (`error_count`)

### Grafana

- **Dashboards**:
  - **API Metrics Dashboard**: Visualizes request counts, prediction counts, and latency.

### Alertmanager

- **Alerts Configured**:
  - **High Latency**: Triggered when the 95th percentile latency exceeds 1 second.
  - **Low Prediction Count**: Triggered when the number of predictions falls below 100 per minute.
  - **High Error Rate**: Triggered when any errors occur within a minute.

- **Notifications**: Configured to send email alerts. Update the `alertmanager.yml` with your email credentials.
