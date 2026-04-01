@echo off
echo ============================================================
echo ML ANOMALY DETECTION - QUICK START
echo ============================================================
echo.

echo [1/3] Checking if model files exist...
if exist "models\anomaly_detection_model.pkl" (
    echo Model files found!
    echo.
    goto :start_service
) else (
    echo Model files not found. Training model first...
    echo.
)

echo [2/3] Training Isolation Forest model...
python train_anomaly_model.py
if errorlevel 1 (
    echo.
    echo ERROR: Model training failed!
    echo Please check the error messages above.
    pause
    exit /b 1
)
echo.

:start_service
echo [3/3] Starting ML Anomaly Detection Service...
echo Service will run on: http://localhost:8002
echo.
echo Press Ctrl+C to stop the service
echo.
python ml_anomaly_service.py

pause
