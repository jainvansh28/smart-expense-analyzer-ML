"""
ML-Based Budget Recommendation Service
Provides REST API for recommending category-wise monthly budgets
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import json
import numpy as np
import pandas as pd
import mysql.connector
from datetime import datetime
from config import DB_CONFIG
import os

app = FastAPI(title="ML Budget Recommendation Service", version="1.0.0")

# Global variables for model and encoders
model = None
category_encoder = None
metadata = None

class BudgetRequest(BaseModel):
    user_id: int

class CategoryBudget(BaseModel):
    category: str
    recommended_budget: float
    historical_avg: float
    consistency_score: float

class BudgetResponse(BaseModel):
    success: bool
    user_id: int
    recommended_budgets: list
    total_recommended: float
    monthly_income: float
    model_confidence: str
    insight: str

# Load models on startup
@app.on_event("startup")
async def load_models():
    global model, category_encoder, metadata
    
    print("=" * 60)
    print("ML BUDGET RECOMMENDATION SERVICE - STARTING")
    print("=" * 60)
    
    try:
        # Check if model files exist
        model_path = 'models/budget_recommendation_model.pkl'
        encoder_path = 'models/budget_category_encoder.pkl'
        metadata_path = 'models/budget_metadata.json'
        
        if not all(os.path.exists(p) for p in [model_path, encoder_path, metadata_path]):
            print("\n⚠️  WARNING: Model files not found!")
            print("Please run: python train_budget_recommendation_model.py")
            print("Service will start but budget recommendations will not work.")
            return
        
        # Load model
        print("\n[1/3] Loading Random Forest model...")
        model = joblib.load(model_path)
        print("✓ Model loaded")
        
        # Load category encoder
        print("\n[2/3] Loading category encoder...")
        category_encoder = joblib.load(encoder_path)
        print(f"✓ Encoder loaded ({len(category_encoder.classes_)} categories)")
        
        # Load metadata
        print("\n[3/3] Loading model metadata...")
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
        print(f"Test R² Score: {metadata['test_score']:.4f}")
        print("=" * 60)
        
        print("\n✓ ML Budget Recommendation Service Ready")
        print("Listening on: http://localhost:8003")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n✗ Error loading models: {e}")
        print("Service will start but budget recommendations will not work.")

@app.get("/")
async def root():
    return {
        "service": "ML Budget Recommendation Service",
        "version": "1.0.0",
        "status": "running",
        "model_loaded": model is not None,
        "endpoint": "/ml/budget-recommendation"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/ml/budget-info")
async def get_model_info():
    """Get information about the budget recommendation model"""
    if model is None or metadata is None:
        raise HTTPException(status_code=503, detail="Model not loaded. Please train the model first.")
    
    return {
        "model_type": metadata['model_type'],
        "training_date": metadata['training_date'],
        "training_samples": metadata['training_samples'],
        "n_users": metadata['n_users'],
        "n_categories": metadata['n_categories'],
        "categories": metadata['categories'],
        "test_score": metadata['test_score'],
        "feature_importance": metadata['feature_importance'][:5]  # Top 5
    }

@app.post("/ml/budget-recommendation", response_model=BudgetResponse)
async def recommend_budget(request: BudgetRequest):
    """
    Recommend category-wise monthly budgets for a user
    
    Returns:
    - success: True if recommendations generated
    - recommended_budgets: List of category budgets
    - total_recommended: Sum of all recommended budgets
    - monthly_income: User's average monthly income
    - model_confidence: High/Medium/Low
    - insight: Personalized insight message
    """
    
    if model is None or category_encoder is None or metadata is None:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Please train the model first by running: python train_budget_recommendation_model.py"
        )
    
    try:
        # Fetch user's historical data
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # Get user's expenses from last 6 months
        expense_query = """
            SELECT 
                category,
                amount,
                date,
                YEAR(date) as year,
                MONTH(date) as month
            FROM expenses
            WHERE user_id = %s
            AND date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
            ORDER BY date DESC
        """
        
        cursor.execute(expense_query, (request.user_id,))
        expenses = cursor.fetchall()
        
        if not expenses:
            cursor.close()
            conn.close()
            raise HTTPException(
                status_code=404,
                detail=f"No expense history found for user {request.user_id}"
            )
        
        expense_df = pd.DataFrame(expenses)
        
        # Convert numeric columns
        for col in ['amount', 'year', 'month']:
            expense_df[col] = pd.to_numeric(expense_df[col], errors='coerce')
        
        # Get user's income from last 6 months
        income_query = """
            SELECT 
                amount,
                YEAR(date) as year,
                MONTH(date) as month
            FROM income
            WHERE user_id = %s
            AND date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
        """
        
        cursor.execute(income_query, (request.user_id,))
        incomes = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Calculate monthly income
        if incomes:
            income_df = pd.DataFrame(incomes)
            income_df['amount'] = pd.to_numeric(income_df['amount'], errors='coerce')
            avg_monthly_income = income_df['amount'].sum() / max(income_df.groupby(['year', 'month']).ngroups, 1)
        else:
            avg_monthly_income = 0
        
        # Calculate category statistics
        category_stats = expense_df.groupby('category').agg({
            'amount': ['sum', 'mean', 'std', 'count']
        }).reset_index()
        
        category_stats.columns = ['category', 'total_spent', 'avg_spent', 'std_spent', 'expense_count']
        
        # Convert to numeric
        for col in ['total_spent', 'avg_spent', 'std_spent', 'expense_count']:
            category_stats[col] = pd.to_numeric(category_stats[col], errors='coerce')
        
        category_stats['std_spent'] = category_stats['std_spent'].fillna(0)
        
        # Calculate monthly averages
        n_months = expense_df.groupby(['year', 'month']).ngroups
        n_months = max(n_months, 1)
        
        category_stats['monthly_avg'] = category_stats['total_spent'] / n_months
        
        # Calculate spending consistency
        category_stats['spending_consistency'] = np.where(
            category_stats['avg_spent'] > 0,
            1 - (category_stats['std_spent'] / (category_stats['avg_spent'] + 1)),
            0
        )
        
        # Calculate percentage of income
        category_stats['pct_of_income'] = np.where(
            avg_monthly_income > 0,
            (category_stats['monthly_avg'] / avg_monthly_income) * 100,
            0
        )
        
        # Generate recommendations for each category
        recommendations = []
        total_recommended = 0
        
        for _, cat_row in category_stats.iterrows():
            category = cat_row['category']
            
            # Check if category is known
            if category not in category_encoder.classes_:
                # Use historical average for unknown categories
                recommended_budget = cat_row['monthly_avg'] * 1.1
            else:
                # Prepare features for prediction
                features = {
                    'user_id': request.user_id,
                    'category_encoded': category_encoder.transform([category])[0],
                    'month': datetime.now().month,
                    'monthly_income': float(avg_monthly_income),
                    'avg_spent': float(cat_row['avg_spent']),
                    'std_spent': float(cat_row['std_spent']),
                    'expense_count': float(cat_row['expense_count']),
                    'spending_consistency': float(cat_row['spending_consistency']),
                    'pct_of_income': float(cat_row['pct_of_income'])
                }
                
                X_pred = pd.DataFrame([features])[metadata['feature_columns']]
                predicted_budget = model.predict(X_pred)[0]
                
                # Add 10% safety buffer
                recommended_budget = predicted_budget * 1.1
            
            # Ensure minimum budget
            recommended_budget = max(recommended_budget, cat_row['monthly_avg'] * 0.8)
            
            recommendations.append({
                "category": category,
                "recommended_budget": round(float(recommended_budget), 2),
                "historical_avg": round(float(cat_row['monthly_avg']), 2),
                "consistency_score": round(float(cat_row['spending_consistency']), 2)
            })
            
            total_recommended += recommended_budget
        
        # Sort by recommended budget (highest first)
        recommendations.sort(key=lambda x: x['recommended_budget'], reverse=True)
        
        # Determine confidence based on data availability
        if n_months >= 6 and len(recommendations) >= 3:
            confidence = "High"
        elif n_months >= 3 and len(recommendations) >= 2:
            confidence = "Medium"
        else:
            confidence = "Low"
        
        # Generate insight
        insight = generate_insight(recommendations, avg_monthly_income, total_recommended, n_months)
        
        # Log recommendation
        print(f"[BUDGET RECOMMENDATION] User {request.user_id} | Categories: {len(recommendations)} | Total: ₹{total_recommended:.2f} | Confidence: {confidence}")
        
        return BudgetResponse(
            success=True,
            user_id=request.user_id,
            recommended_budgets=recommendations,
            total_recommended=round(float(total_recommended), 2),
            monthly_income=round(float(avg_monthly_income), 2),
            model_confidence=confidence,
            insight=insight
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error generating budget recommendation: {e}")
        raise HTTPException(status_code=500, detail=f"Budget recommendation failed: {str(e)}")

def generate_insight(recommendations, monthly_income, total_recommended, n_months):
    """Generate personalized insight based on recommendations"""
    
    if len(recommendations) == 0:
        return "Start tracking expenses to get personalized budget recommendations."
    
    # Find most volatile category (lowest consistency)
    volatile_cat = min(recommendations, key=lambda x: x['consistency_score'])
    
    # Find highest spending category
    top_cat = recommendations[0]
    
    # Calculate budget utilization
    if monthly_income > 0:
        utilization = (total_recommended / monthly_income) * 100
    else:
        utilization = 0
    
    # Generate insight
    insight_parts = []
    
    # Data quality insight
    if n_months >= 6:
        insight_parts.append(f"Based on {n_months} months of spending data, ")
    else:
        insight_parts.append(f"Based on {n_months} months of data (limited history), ")
    
    # Top category insight
    insight_parts.append(f"your highest spending is on {top_cat['category']} (₹{top_cat['recommended_budget']:.0f}/month). ")
    
    # Volatility insight
    if volatile_cat['consistency_score'] < 0.5:
        insight_parts.append(f"{volatile_cat['category']} spending is volatile, so a conservative budget is recommended. ")
    
    # Budget utilization insight
    if utilization > 90:
        insight_parts.append("⚠️ Recommended budgets use most of your income. Consider increasing income or reducing expenses.")
    elif utilization > 70:
        insight_parts.append("Your budgets are balanced but leave limited room for savings.")
    else:
        insight_parts.append(f"✓ Good balance! You have ~{100-utilization:.0f}% of income available for savings.")
    
    return "".join(insight_parts)

if __name__ == "__main__":
    import uvicorn
    print("\nStarting ML Budget Recommendation Service on port 8003...")
    uvicorn.run(app, host="0.0.0.0", port=8003)
