"""
ML-Based Budget Recommendation Training Script
Uses Random Forest Regressor to recommend category-wise monthly budgets
"""

import mysql.connector
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import joblib
import json
from datetime import datetime
from config import DB_CONFIG

print("=" * 60)
print("ML BUDGET RECOMMENDATION - TRAINING SCRIPT")
print("=" * 60)

# Database connection
print("\n[1/8] Connecting to MySQL database...")
try:
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    print("✓ Connected successfully")
except Exception as e:
    print(f"✗ Database connection failed: {e}")
    exit(1)

# Fetch expense data
print("\n[2/8] Fetching expense and income data...")
expense_query = """
    SELECT 
        user_id,
        amount,
        category,
        date,
        YEAR(date) as year,
        MONTH(date) as month
    FROM expenses
    ORDER BY date DESC
"""

income_query = """
    SELECT 
        user_id,
        amount,
        date,
        YEAR(date) as year,
        MONTH(date) as month
    FROM income
    ORDER BY date DESC
"""

try:
    # Fetch expenses
    cursor.execute(expense_query)
    expenses = cursor.fetchall()
    expense_df = pd.DataFrame(expenses)
    
    # Convert numeric columns
    numeric_cols = ['amount', 'user_id', 'year', 'month']
    for col in numeric_cols:
        if col in expense_df.columns:
            expense_df[col] = pd.to_numeric(expense_df[col], errors='coerce')
    
    print(f"✓ Loaded {len(expense_df)} expense records")
    
    # Fetch income
    cursor.execute(income_query)
    incomes = cursor.fetchall()
    income_df = pd.DataFrame(incomes)
    
    # Convert numeric columns
    for col in numeric_cols:
        if col in income_df.columns:
            income_df[col] = pd.to_numeric(income_df[col], errors='coerce')
    
    print(f"✓ Loaded {len(income_df)} income records")
    
except Exception as e:
    print(f"✗ Failed to fetch data: {e}")
    conn.close()
    exit(1)

cursor.close()
conn.close()

# Data validation
print("\n[3/8] Validating and preparing data...")
if len(expense_df) < 30:
    print(f"✗ Insufficient expense data: {len(expense_df)} records (minimum 30 required)")
    exit(1)

# Remove null values
expense_df = expense_df.dropna()
income_df = income_df.dropna()

print(f"✓ Data validated")
print(f"  - Expense records: {len(expense_df)}")
print(f"  - Income records: {len(income_df)}")
print(f"  - Users: {expense_df['user_id'].nunique()}")
print(f"  - Categories: {expense_df['category'].nunique()}")

# Feature engineering
print("\n[4/8] Engineering features for budget recommendation...")

# Calculate monthly income per user
monthly_income = income_df.groupby(['user_id', 'year', 'month'])['amount'].sum().reset_index()
monthly_income.columns = ['user_id', 'year', 'month', 'monthly_income']
monthly_income['monthly_income'] = pd.to_numeric(monthly_income['monthly_income'], errors='coerce')

# Calculate monthly category spending per user
monthly_category_spending = expense_df.groupby(['user_id', 'year', 'month', 'category'])['amount'].agg([
    'sum', 'mean', 'std', 'count'
]).reset_index()
monthly_category_spending.columns = ['user_id', 'year', 'month', 'category', 'total_spent', 'avg_spent', 'std_spent', 'expense_count']

# Convert to numeric
for col in ['total_spent', 'avg_spent', 'std_spent', 'expense_count']:
    monthly_category_spending[col] = pd.to_numeric(monthly_category_spending[col], errors='coerce')

# Fill NaN std with 0
monthly_category_spending['std_spent'] = monthly_category_spending['std_spent'].fillna(0)

# Merge with income data
budget_data = monthly_category_spending.merge(
    monthly_income, 
    on=['user_id', 'year', 'month'], 
    how='left'
)

# Fill missing income with 0
budget_data['monthly_income'] = budget_data['monthly_income'].fillna(0)

# Calculate additional features
budget_data['income_to_spending_ratio'] = np.where(
    budget_data['total_spent'] > 0,
    budget_data['monthly_income'] / budget_data['total_spent'],
    0
)

# Calculate spending consistency (lower std = more consistent)
budget_data['spending_consistency'] = np.where(
    budget_data['avg_spent'] > 0,
    1 - (budget_data['std_spent'] / (budget_data['avg_spent'] + 1)),
    0
)

# Calculate percentage of income spent on category
budget_data['pct_of_income'] = np.where(
    budget_data['monthly_income'] > 0,
    (budget_data['total_spent'] / budget_data['monthly_income']) * 100,
    0
)

print(f"✓ Features engineered:")
print(f"  - monthly_income: user's monthly income")
print(f"  - total_spent: total spent in category that month")
print(f"  - avg_spent: average transaction amount")
print(f"  - std_spent: spending variance")
print(f"  - expense_count: number of expenses")
print(f"  - spending_consistency: how consistent spending is")
print(f"  - pct_of_income: percentage of income spent")

# Encode categorical features
print("\n[5/8] Encoding categorical features...")

category_encoder = LabelEncoder()
budget_data['category_encoded'] = category_encoder.fit_transform(budget_data['category'])

# Prepare training data
# Target: recommended budget = total_spent (what they actually spent)
# We'll train the model to predict appropriate spending based on patterns

feature_columns = [
    'user_id',
    'category_encoded',
    'month',
    'monthly_income',
    'avg_spent',
    'std_spent',
    'expense_count',
    'spending_consistency',
    'pct_of_income'
]

X = budget_data[feature_columns].copy()
y = budget_data['total_spent'].copy()

# Handle any remaining NaN
X = X.fillna(0)
y = y.fillna(0)

print(f"✓ Features encoded")
print(f"  - Training samples: {len(X)}")
print(f"  - Feature columns: {len(feature_columns)}")

# Split data for validation
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train Random Forest model
print("\n[6/8] Training Random Forest Regressor...")

model = RandomForestRegressor(
    n_estimators=100,
    max_depth=10,
    min_samples_split=5,
    min_samples_leaf=2,
    random_state=42,
    n_jobs=-1
)

model.fit(X_train, y_train)

# Evaluate model
train_score = model.score(X_train, y_train)
test_score = model.score(X_test, y_test)

print(f"✓ Model trained successfully")
print(f"  - Algorithm: Random Forest Regressor")
print(f"  - Estimators: 100")
print(f"  - Training R² score: {train_score:.4f}")
print(f"  - Testing R² score: {test_score:.4f}")

# Feature importance
feature_importance = pd.DataFrame({
    'feature': feature_columns,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

print(f"\n  Top 5 Important Features:")
for idx, row in feature_importance.head(5).iterrows():
    print(f"    {row['feature']}: {row['importance']:.4f}")

# Save model and encoders
print("\n[7/8] Saving model files...")

try:
    # Save model
    joblib.dump(model, 'models/budget_recommendation_model.pkl')
    print("✓ Saved: models/budget_recommendation_model.pkl")
    
    # Save category encoder
    joblib.dump(category_encoder, 'models/budget_category_encoder.pkl')
    print("✓ Saved: models/budget_category_encoder.pkl")
    
    # Calculate category statistics for recommendations
    category_stats = budget_data.groupby('category').agg({
        'total_spent': ['mean', 'std', 'min', 'max'],
        'spending_consistency': 'mean',
        'pct_of_income': 'mean'
    }).reset_index()
    
    category_stats.columns = ['_'.join(col).strip('_') for col in category_stats.columns.values]
    category_stats_dict = category_stats.to_dict('records')
    
    # Save metadata
    metadata = {
        'model_type': 'RandomForestRegressor',
        'training_date': datetime.now().isoformat(),
        'training_samples': len(budget_data),
        'n_users': int(budget_data['user_id'].nunique()),
        'n_categories': int(budget_data['category'].nunique()),
        'categories': category_encoder.classes_.tolist(),
        'feature_columns': feature_columns,
        'train_score': float(train_score),
        'test_score': float(test_score),
        'n_estimators': 100,
        'category_statistics': category_stats_dict,
        'feature_importance': feature_importance.to_dict('records')
    }
    
    with open('models/budget_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    print("✓ Saved: models/budget_metadata.json")
    
except Exception as e:
    print(f"✗ Failed to save model files: {e}")
    exit(1)

# Generate sample recommendations
print("\n[8/8] Generating sample recommendations...")

# Get a sample user
sample_user_id = budget_data['user_id'].iloc[0]
sample_user_data = budget_data[budget_data['user_id'] == sample_user_id]

if len(sample_user_data) > 0:
    print(f"\nSample Budget Recommendations for User {int(sample_user_id)}:")
    print("-" * 60)
    
    # Get user's average monthly income
    avg_income = sample_user_data['monthly_income'].mean()
    
    # Generate recommendations for each category
    for category in category_encoder.classes_:
        # Get historical data for this category
        cat_data = sample_user_data[sample_user_data['category'] == category]
        
        if len(cat_data) > 0:
            # Prepare features for prediction
            features = {
                'user_id': sample_user_id,
                'category_encoded': category_encoder.transform([category])[0],
                'month': datetime.now().month,
                'monthly_income': avg_income,
                'avg_spent': cat_data['avg_spent'].mean(),
                'std_spent': cat_data['std_spent'].mean(),
                'expense_count': cat_data['expense_count'].mean(),
                'spending_consistency': cat_data['spending_consistency'].mean(),
                'pct_of_income': cat_data['pct_of_income'].mean()
            }
            
            X_pred = pd.DataFrame([features])[feature_columns]
            predicted_budget = model.predict(X_pred)[0]
            
            # Add safety margin (10% buffer)
            recommended_budget = predicted_budget * 1.1
            
            print(f"  {category:15} → ₹{recommended_budget:,.2f}")

print("\n" + "=" * 60)
print("TRAINING COMPLETE ✓")
print("=" * 60)
print("\nModel files saved in 'models/' directory")
print("Ready to use for budget recommendation API")
print("\nNext steps:")
print("1. Add endpoint to ML service")
print("2. Test endpoint: POST http://localhost:8003/ml/budget-recommendation")
print("=" * 60)
