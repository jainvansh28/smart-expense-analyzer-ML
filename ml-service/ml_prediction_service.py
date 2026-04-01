"""
ML Prediction Service - Separate from rule-based system
Uses trained model for expense predictions
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
import numpy as np
import joblib
import json
import os
from datetime import datetime

app = FastAPI(title="ML Expense Prediction Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Model paths
MODEL_PATH = 'models/expense_prediction_model.pkl'
ENCODERS_PATH = 'models/category_encoder.pkl'
METADATA_PATH = 'models/model_metadata.json'

# Global variables for loaded model
model = None
category_encoder = None
feature_columns = None
model_metadata = None

def load_model():
    """Load trained model and encoders"""
    global model, category_encoder, feature_columns, model_metadata
    
    try:
        if not os.path.exists(MODEL_PATH):
            print("⚠ Model not found. Please run train_model.py first.")
            return False
        
        model = joblib.load(MODEL_PATH)
        category_encoder = joblib.load(ENCODERS_PATH)
        
        with open(METADATA_PATH, 'r') as f:
            model_metadata = json.load(f)
        
        feature_columns = model_metadata['feature_columns']
        
        print("✓ ML Model loaded successfully")
        print(f"  Trained at: {model_metadata['trained_at']}")
        print(f"  Test MAE: ₹{model_metadata['metrics']['test_mae']:.2f}")
        print(f"  Test R²: {model_metadata['metrics']['test_r2']:.4f}")
        
        return True
    
    except Exception as e:
        print(f"✗ Error loading model: {e}")
        return False

# Load model on startup
@app.on_event("startup")
async def startup_event():
    load_model()

class ExpenseRecord(BaseModel):
    amount: float
    category: str
    date: str

class MLPredictionRequest(BaseModel):
    user_id: int
    expenses: List[ExpenseRecord]
    incomes: Optional[List[ExpenseRecord]] = []  # Add income data
    target_month: Optional[int] = None
    target_year: Optional[int] = None

class CategoryPrediction(BaseModel):
    category: str
    predicted_amount: float
    confidence: str

class MLPredictionResponse(BaseModel):
    user_id: int
    prediction_month: str
    total_predicted_expense: float
    category_predictions: List[CategoryPrediction]
    model_version: str
    prediction_confidence: str
    metrics: dict
    # Add predicted savings fields
    avg_monthly_income: Optional[float] = None
    predicted_savings: Optional[float] = None
    income_months_analyzed: Optional[int] = None

@app.get("/")
def read_root():
    return {
        "service": "ML Expense Prediction Service",
        "status": "running",
        "model_loaded": model is not None
    }

@app.get("/model/info")
def get_model_info():
    """Get information about the loaded model"""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded. Please train the model first.")
    
    return {
        "model_type": model_metadata.get('model_type', 'Unknown'),
        "trained_at": model_metadata.get('trained_at', 'Unknown'),
        "version": model_metadata.get('version', 'Unknown'),
        "metrics": model_metadata.get('metrics', {}),
        "feature_columns": feature_columns
    }

@app.post("/ml/predict", response_model=MLPredictionResponse)
def predict_ml(request: MLPredictionRequest):
    """
    ML-based expense prediction using trained model
    Separate from rule-based prediction system
    """
    if model is None:
        raise HTTPException(
            status_code=503,
            detail="ML model not loaded. Please run train_model.py first."
        )
    
    try:
        # Convert expenses to DataFrame
        df = pd.DataFrame([{
            'amount': exp.amount,
            'category': exp.category,
            'date': datetime.strptime(exp.date, '%Y-%m-%d')
        } for exp in request.expenses])
        
        if len(df) == 0:
            raise HTTPException(status_code=400, detail="No expense data provided")
        
        # Extract year and month
        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month
        
        # Determine target month
        if request.target_month and request.target_year:
            target_month = request.target_month
            target_year = request.target_year
        else:
            # Predict next month
            latest_date = df['date'].max()
            next_month = latest_date.month + 1
            target_year = latest_date.year
            if next_month > 12:
                next_month = 1
                target_year += 1
            target_month = next_month
        
        # Get unique categories from user's history
        user_categories = df['category'].unique()
        
        # Calculate features for each category
        category_predictions = []
        
        for category in user_categories:
            try:
                # Filter data for this category
                cat_df = df[df['category'] == category].copy()
                
                # Calculate rolling average
                cat_df = cat_df.sort_values('date')
                rolling_avg = cat_df['amount'].tail(3).mean()
                
                # Calculate total monthly spending
                monthly_totals = df.groupby(['year', 'month'])['amount'].sum()
                avg_monthly_total = monthly_totals.mean()
                
                # Calculate category percentage
                cat_monthly = cat_df.groupby(['year', 'month'])['amount'].sum()
                cat_percentage = (cat_monthly.mean() / avg_monthly_total * 100) if avg_monthly_total > 0 else 0
                
                # Encode category
                if category in category_encoder.classes_:
                    category_encoded = category_encoder.transform([category])[0]
                else:
                    # Unknown category, use mean prediction
                    category_encoded = 0
                
                # Create features
                month_sin = np.sin(2 * np.pi * target_month / 12)
                month_cos = np.cos(2 * np.pi * target_month / 12)
                
                # Create feature vector
                features = pd.DataFrame([{
                    'user_id': request.user_id,
                    'month': target_month,
                    'category_encoded': category_encoded,
                    'month_sin': month_sin,
                    'month_cos': month_cos,
                    'rolling_avg_3m': rolling_avg,
                    'category_percentage': cat_percentage
                }])
                
                # Ensure feature order matches training
                features = features[feature_columns]
                
                # Predict
                predicted_amount = model.predict(features)[0]
                predicted_amount = max(0, predicted_amount)  # Ensure non-negative
                
                # Determine confidence based on historical data
                if len(cat_df) >= 6:
                    confidence = "High"
                elif len(cat_df) >= 3:
                    confidence = "Medium"
                else:
                    confidence = "Low"
                
                category_predictions.append(CategoryPrediction(
                    category=category,
                    predicted_amount=round(predicted_amount, 2),
                    confidence=confidence
                ))
            
            except Exception as e:
                print(f"Warning: Could not predict for category {category}: {e}")
                continue
        
        # Calculate total predicted expense
        total_predicted = sum(cp.predicted_amount for cp in category_predictions)
        
        # Calculate predicted savings based on income data
        avg_monthly_income = None
        predicted_savings = None
        income_months_analyzed = None
        
        print(f"=== INCOME ANALYSIS DEBUG for user {request.user_id} ===")
        print(f"Income records received: {len(request.incomes) if request.incomes else 0}")
        
        if request.incomes and len(request.incomes) > 0:
            # Convert incomes to DataFrame
            income_df = pd.DataFrame([{
                'amount': inc.amount,
                'date': datetime.strptime(inc.date, '%Y-%m-%d')
            } for inc in request.incomes])
            
            print(f"Total income records loaded: {len(income_df)}")
            print(f"Income date range: {income_df['date'].min()} to {income_df['date'].max()}")
            
            # Calculate monthly income totals using INCOME DATES ONLY
            income_df['year'] = income_df['date'].dt.year
            income_df['month'] = income_df['date'].dt.month
            
            # Group by year-month to get unique months
            monthly_income_totals = income_df.groupby(['year', 'month'])['amount'].sum()
            
            print(f"Unique income months found: {len(monthly_income_totals)}")
            print(f"Monthly income totals: {monthly_income_totals.to_dict()}")
            
            if len(monthly_income_totals) > 0:
                total_income = monthly_income_totals.sum()
                avg_monthly_income = monthly_income_totals.mean()
                income_months_analyzed = len(monthly_income_totals)
                predicted_savings = max(0, avg_monthly_income - total_predicted)
                
                print(f"Total income across all months: ₹{total_income:.2f}")
                print(f"Average monthly income: ₹{avg_monthly_income:.2f}")
                print(f"Income months analyzed: {income_months_analyzed}")
                print(f"Predicted monthly expense: ₹{total_predicted:.2f}")
                print(f"Predicted savings: ₹{predicted_savings:.2f}")
            else:
                print("ERROR: No monthly income totals calculated despite having income records!")
        else:
            print("No income data provided - predicted savings will be null")
        
        # Determine overall confidence
        high_conf_count = sum(1 for cp in category_predictions if cp.confidence == "High")
        if high_conf_count >= len(category_predictions) * 0.7:
            overall_confidence = "High"
        elif high_conf_count >= len(category_predictions) * 0.4:
            overall_confidence = "Medium"
        else:
            overall_confidence = "Low"
        
        return MLPredictionResponse(
            user_id=request.user_id,
            prediction_month=f"{target_year}-{target_month:02d}",
            total_predicted_expense=round(total_predicted, 2),
            category_predictions=category_predictions,
            model_version=model_metadata.get('version', '1.0'),
            prediction_confidence=overall_confidence,
            metrics={
                "categories_predicted": len(category_predictions),
                "historical_months": len(df['date'].dt.to_period('M').unique()),
                "total_expenses_analyzed": len(df)
            },
            avg_monthly_income=round(avg_monthly_income, 2) if avg_monthly_income is not None else None,
            predicted_savings=round(predicted_savings, 2) if predicted_savings is not None else None,
            income_months_analyzed=income_months_analyzed
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ML prediction failed: {str(e)}")

@app.post("/ml/retrain")
def trigger_retrain():
    """Trigger model retraining (placeholder for future automation)"""
    return {
        "message": "To retrain the model, run: python train_model.py",
        "status": "manual_training_required"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
