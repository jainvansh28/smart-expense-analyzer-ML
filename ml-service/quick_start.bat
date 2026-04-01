@echo off
echo ==========================================
echo ML Service Quick Start
echo ==========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo X Python not found. Please install Python 3.8+
    exit /b 1
)

echo √ Python found

REM Install dependencies
echo.
echo Installing dependencies...
pip install -r requirements.txt

if errorlevel 1 (
    echo X Failed to install dependencies
    exit /b 1
)

echo √ Dependencies installed

REM Train model
echo.
echo Training ML model...
python train_model.py

if errorlevel 1 (
    echo X Model training failed
    exit /b 1
)

echo.
echo √ Model trained successfully

REM Start ML service
echo.
echo Starting ML Prediction Service on port 8001...
echo Press Ctrl+C to stop
echo.
python ml_prediction_service.py
