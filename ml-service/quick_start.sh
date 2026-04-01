#!/bin/bash

echo "=========================================="
echo "ML Service Quick Start"
echo "=========================================="
echo ""

# Check if Python is installed
if ! command -v python &> /dev/null; then
    echo "❌ Python not found. Please install Python 3.8+"
    exit 1
fi

echo "✓ Python found"

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✓ Dependencies installed"

# Train model
echo ""
echo "Training ML model..."
python train_model.py

if [ $? -ne 0 ]; then
    echo "❌ Model training failed"
    exit 1
fi

echo ""
echo "✓ Model trained successfully"

# Start ML service
echo ""
echo "Starting ML Prediction Service on port 8001..."
echo "Press Ctrl+C to stop"
echo ""
python ml_prediction_service.py
