#!/bin/bash

echo "============================================================"
echo "ML ANOMALY DETECTION - QUICK START"
echo "============================================================"
echo ""

echo "[1/3] Checking if model files exist..."
if [ -f "models/anomaly_detection_model.pkl" ]; then
    echo "✓ Model files found!"
    echo ""
else
    echo "Model files not found. Training model first..."
    echo ""
    
    echo "[2/3] Training Isolation Forest model..."
    python3 train_anomaly_model.py
    
    if [ $? -ne 0 ]; then
        echo ""
        echo "ERROR: Model training failed!"
        echo "Please check the error messages above."
        exit 1
    fi
    echo ""
fi

echo "[3/3] Starting ML Anomaly Detection Service..."
echo "Service will run on: http://localhost:8002"
echo ""
echo "Press Ctrl+C to stop the service"
echo ""

python3 ml_anomaly_service.py
