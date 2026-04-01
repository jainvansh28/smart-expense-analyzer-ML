#!/bin/bash

echo "============================================================"
echo "ML BUDGET RECOMMENDATION - QUICK START"
echo "============================================================"
echo ""

echo "[1/3] Checking if model files exist..."
if [ -f "models/budget_recommendation_model.pkl" ]; then
    echo "✓ Model files found!"
    echo ""
else
    echo "Model files not found. Training model first..."
    echo ""
    
    echo "[2/3] Training Random Forest model..."
    python3 train_budget_recommendation_model.py
    
    if [ $? -ne 0 ]; then
        echo ""
        echo "ERROR: Model training failed!"
        echo "Please check the error messages above."
        exit 1
    fi
    echo ""
fi

echo "[3/3] Starting ML Budget Recommendation Service..."
echo "Service will run on: http://localhost:8003"
echo ""
echo "Press Ctrl+C to stop the service"
echo ""

python3 ml_budget_service.py
