#!/bin/bash
# Entry point script to initialize the database and start the server

# Exit immediately if a command exits with a non-zero status
set -e

# Navigate to the app directory
cd /app

# Path to the model
MODEL_PATH="/models/model.joblib"

# Wait until the model file is present
echo "Checking for model at $MODEL_PATH"
while [ ! -f $MODEL_PATH ]; do
    echo "Waiting for model file at $MODEL_PATH..."
    sleep 5
done

# Initialize the database
echo "Initializing the database..."
python -c "from database import create_db_and_tables; create_db_and_tables()"

# Start the application using Uvicorn
echo "Starting the API server..."
uvicorn main:app --host 0.0.0.0 --port 8000
