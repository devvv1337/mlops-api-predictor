#!/bin/bash
# Entry point script to initialize the database and start the server

# Exit immediately if a command exits with a non-zero status
set -e

# Navigate to the project root directory
cd /app

# Pull the model from the DVC remote
echo "Pulling model from DVC remote..."
dvc pull models/model.joblib

# Initialize the database
echo "Initializing the database..."
python -c "from app.database import create_db_and_tables; create_db_and_tables()"

# Start the application using Uvicorn
echo "Starting the API server..."
uvicorn app.main:app --host 0.0.0.0 --port 8000
