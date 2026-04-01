"""
ML-Based Anomaly Detection Service
Provides REST API for detecting unusual expense patterns using Isolation Forest
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import json
import numpy as np
import mysql.connector
from datetime import datetime, timedelta
from config import DB_CONFIG
import os

app = FastAPI(title="ML Anomaly Detection Service", version="1.0.0")

# Global variables for model and encoders
model = None
scaler = None
category_encoder = None
metadata = None

class AnomalyRequest(BaseModel):
    user_id: int
    amount: float
    category: str
    date: str  # Format: YYYY-MM-DD

class AnomalyResponse(BaseModel):
    is_anomaly: bool
    anomaly_score: float
    confidence: str
    anomaly_message: str
    details: dict

# Load models on startup
@app.on_event("startup")
async def load_models():
    global model, scaler, category_encoder, metadata
    
    print("=" * 60)
    print("ML ANOMALY DETECTION SERVICE - STARTING")
    print("=" * 60)
    
    try:
        # Check if model files exist
        model_path = 'models/anomaly_detection_model.pkl'
        scaler_path = 'models/anomaly_scaler.pkl'
        encoder_path = 'models/anomaly_category_encoder.pkl'
        metadata_path = 'models/anomaly_metadata.json'
        
        if not all(os.path.exists(p) for p in [model_path, scaler_path, encoder_path, metadata_path]):
            print("\n⚠️  WARNING: Model files not found!")
            print("Please run: python train_anomaly_model.py")
            print("Service will start but anomaly detection will not work.")
            return
        
        # Load model
        print("\n[1/4] Loading Isolation Forest model...")
        model = joblib.load(model_path)
        print("✓ Model loaded")
        
        # Load scaler
        print("\n[2/4] Loading feature scaler...")
        scaler = joblib.load(scaler_path)
        print("✓ Scaler loaded")
        
        # Load category encoder
        print("\n[3/4] Loading category encoder...")
        category_encoder = joblib.load(encoder_path)
        print(f"✓ Encoder loaded ({len(category_encoder.classes_)} categories)")
        
        # Load metadata
        print("\n[4/4] Loading model metadata...")
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        print("✓ Metadata loaded")
        
        print("\n" + "=" * 60)
        print("MODEL INFORMATION")
        print("=" * 60)
        print(f"Model Type: {metadata['model_type']}")
        print(f"Training Date: {metadata['training_date']}")
        print(f"Training Samples: {metadata['training_samples']}")
        print(f"Users: {metadata['n_users']}")
        print(f"Categories: {metadata['n_categories']}")
        print(f"Contamination Rate: {metadata['contamination'] * 100}%")
        print("=" * 60)
        
        print("\n✓ ML Anomaly Detection Service Ready")
        print("Listening on: http://localhost:8002")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n✗ Error loading models: {e}")
        print("Service will start but anomaly detection will not work.")

@app.get("/")
async def root():
    return {
        "service": "ML Anomaly Detection Service",
        "version": "1.0.0",
        "status": "running",
        "model_loaded": model is not None,
        "endpoint": "/ml/detect-anomaly"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/ml/anomaly-info")
async def get_model_info():
    """Get information about the anomaly detection model"""
    if model is None or metadata is None:
        raise HTTPException(status_code=503, detail="Model not loaded. Please train the model first.")
    
    return {
        "model_type": metadata['model_type'],
        "training_date": metadata['training_date'],
        "training_samples": metadata['training_samples'],
        "n_users": metadata['n_users'],
        "n_categories": metadata['n_categories'],
        "categories": metadata['categories'],
        "contamination": metadata['contamination'],
        "date_range": metadata['date_range']
    }

@app.post("/ml/detect-anomaly", response_model=AnomalyResponse)
async def detect_anomaly(request: AnomalyRequest):
    """
    Detect if an expense is anomalous using ML model
    
    Returns:
    - is_anomaly: True if expense is unusual
    - anomaly_score: Score from model (lower = more anomalous)
    - confidence: High/Medium/Low
    - anomaly_message: Human-readable message
    - details: Additional information
    """
    
    if model is None or scaler is None or category_encoder is None:
        raise HTTPException(
            status_code=503, 
            detail="Model not loaded. Please train the model first by running: python train_anomaly_model.py"
        )
    
    try:
        # Parse date
        expense_date = datetime.strptime(request.date, '%Y-%m-%d')
        
        # Fetch user's historical data for this category
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # Get user's category statistics
        six_months_ago = (expense_date - timedelta(days=180)).strftime('%Y-%m-%d')
        
        query = """
            SELECT 
                AVG(amount) as avg_amount,
                STDDEV(amount) as std_amount,
                COUNT(*) as expense_count
            FROM expenses
            WHERE user_id = %s 
            AND category = %s
            AND date >= %s
            AND date < %s
        """
        
        cursor.execute(query, (request.user_id, request.category, six_months_ago, request.date))
        stats = cursor.fetchone()
        
        # Get monthly spending
        query_monthly = """
            SELECT SUM(amount) as monthly_total
            FROM expenses
            WHERE user_id = %s
            AND YEAR(date) = %s
            AND MONTH(date) = %s
        """
        
        cursor.execute(query_monthly, (request.user_id, expense_date.year, expense_date.month))
        monthly = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        # Calculate features
        avg_amount = float(stats['avg_amount']) if stats['avg_amount'] else request.amount
        std_amount = float(stats['std_amount']) if stats['std_amount'] else 1.0
        expense_count = int(stats['expense_count']) if stats['expense_count'] else 1
        monthly_total = float(monthly['monthly_total']) if monthly['monthly_total'] else request.amount
        
        # Calculate derived features
        amount_deviation = (request.amount - avg_amount) / (std_amount + 1)
        pct_of_monthly = (request.amount / monthly_total) * 100 if monthly_total > 0 else 0
        
        # Encode category
        if request.category in category_encoder.classes_:
            category_encoded = category_encoder.transform([request.category])[0]
        else:
            # Unknown category - use most common category encoding
            category_encoded = 0
        
        # Prepare feature vector
        features = np.array([[
            request.amount,
            category_encoded,
            expense_date.month,
            expense_date.isoweekday(),
            amount_deviation,
            pct_of_monthly,
            expense_count
        ]])
        
        # Scale features
        features_scaled = scaler.transform(features)
        
        # Predict
        prediction = model.predict(features_scaled)[0]
        anomaly_score = model.score_samples(features_scaled)[0]
        
        # Determine if anomaly
        is_anomaly = prediction == -1
        
        # Calculate confidence based on anomaly score
        # Scores typically range from -0.5 to 0.5
        # More negative = more anomalous
        if anomaly_score < -0.3:
            confidence = "High"
        elif anomaly_score < -0.1:
            confidence = "Medium"
        else:
            confidence = "Low"
        
        # Generate message
        if is_anomaly:
            if amount_deviation > 2:
                anomaly_message = f"⚠️ Unusual spending detected! This ₹{request.amount:.2f} {request.category} expense is significantly higher than your typical spending pattern. ML model detected this as anomalous with {confidence.lower()} confidence."
            elif pct_of_monthly > 30:
                anomaly_message = f"⚠️ Large expense alert! This ₹{request.amount:.2f} represents {pct_of_monthly:.1f}% of your monthly spending. ML model flagged this as unusual."
            else:
                anomaly_message = f"⚠️ Anomaly detected! This ₹{request.amount:.2f} {request.category} expense differs from your learned spending patterns. ML confidence: {confidence}."
        else:
            anomaly_message = f"✓ Normal expense. This ₹{request.amount:.2f} {request.category} expense is within your typical spending range."
        
        # Build response
        response = AnomalyResponse(
            is_anomaly=is_anomaly,
            anomaly_score=float(anomaly_score),
            confidence=confidence,
            anomaly_message=anomaly_message,
            details={
                "amount": request.amount,
                "category": request.category,
                "avg_amount": round(avg_amount, 2),
                "deviation": round(amount_deviation, 2),
                "pct_of_monthly": round(pct_of_monthly, 2),
                "expense_count": expense_count,
                "prediction": "anomaly" if is_anomaly else "normal"
            }
        )
        
        # Log detection
        print(f"[ANOMALY CHECK] User {request.user_id} | {request.category} | ₹{request.amount:.2f} | Result: {'ANOMALY' if is_anomaly else 'NORMAL'} | Score: {anomaly_score:.4f}")
        
        return response
        
    except Exception as e:
        print(f"Error in anomaly detection: {e}")
        raise HTTPException(status_code=500, detail=f"Anomaly detection failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("\nStarting ML Anomaly Detection Service on port 8002...")
    uvicorn.run(app, host="0.0.0.0", port=8002)
