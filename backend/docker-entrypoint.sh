#!/bin/bash
set -e

echo "🌸 BloomWatch Backend Starting..."

# Check if models exist, if not, train them
if [ ! -d "/app/models/almond" ] || [ ! -d "/app/models/apple" ] || [ ! -d "/app/models/cherry" ]; then
    echo "⚠️  Models not found. Training models (this may take 10-15 minutes)..."
    python train_models.py
    echo "✓ Models trained successfully!"
else
    echo "✓ Models found, skipping training"
fi

# Start the API
echo "🚀 Starting FastAPI server..."
exec uvicorn main:app --host 0.0.0.0 --port 8000

