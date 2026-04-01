@echo off
echo ============================================================
echo ML BUDGET RECOMMENDATION - QUICK START
echo ============================================================
echo.

echo [1/3] Checking if model files exist...
if exist "models\budget_recommendation_model.pkl" (
    echo Model files found!
    echo.
    goto :start_service
) else (
    echo Model files not found. Training model first...
    echo.
)

echo [2/3] Training Random Forest model...
python train_budget_recommendation_model.py
if errorlevel 1 (
    echo.
    echo ERROR: Model training failed!
    echo Please check the error messages above.
    pause
    exit /b 1
)
echo.

:start_service
echo [3/3] Starting ML Budget Recommendation Service...
echo Service will run on: http://localhost:8003
echo.
echo Press Ctrl+C to stop the service
echo.
python ml_budget_service.py

pause
