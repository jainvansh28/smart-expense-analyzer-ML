"""
ML-Based Anomaly Detection Training Script
Uses Isolation Forest to detect unusual expense patterns
"""

import mysql.connector
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import LabelEncoder, StandardScaler
import joblib
import json
from datetime import datetime
from config import DB_CONFIG

print("=" * 60)
print("ML ANOMALY DETECTION - TRAINING SCRIPT")
print("=" * 60)

# Database connection
print("\n[1/7] Connecting to MySQL database...")
try:
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    print("✓ Connected successfully")
except Exception as e:
    print(f"✗ Database connection failed: {e}")
    exit(1)

# Fetch expense data
print("\n[2/7] Fetching expense data from database...")
query = """
    SELECT 
        user_id,
        amount,
        category,
        date,
        YEAR(date) as year,
        MONTH(date) as month,
        DAYOFWEEK(date) as day_of_week
    FROM expenses
    ORDER BY date DESC
"""

try:
    cursor.execute(query)
    expenses = cursor.fetchall()
    df = pd.DataFrame(expenses)
    print(f"✓ Loaded {len(df)} expense records")
    print(f"  - Users: {df['user_id'].nunique()}")
    print(f"  - Categories: {df['category'].nunique()}")
    print(f"  - Date range: {df['date'].min()} to {df['date'].max()}")
except Exception as e:
    print(f"✗ Failed to fetch data: {e}")
    conn.close()
    exit(1)

# Close database connection
cursor.close()
conn.close()

# Data validation
print("\n[3/7] Validating and preparing data...")
if len(df) < 50:
    print(f"✗ Insufficient data: {len(df)} records (minimum 50 required)")
    exit(1)

# Remove any null values
df = df.dropna()

# Convert decimal.Decimal columns to float
print("Converting numeric columns to float...")
numeric_columns = ['amount', 'user_id', 'year', 'month', 'day_of_week']
for col in numeric_columns:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

print(f"✓ Data validated: {len(df)} records ready for training")

# Feature engineering
print("\n[4/7] Engineering features...")

# Calculate user-category statistics
user_category_stats = df.groupby(['user_id', 'category'])['amount'].agg([
    'mean', 'std', 'count'
]).reset_index()
user_category_stats.columns = ['user_id', 'category', 'avg_amount', 'std_amount', 'expense_count']

# Merge stats back to main dataframe
df = df.merge(user_category_stats, on=['user_id', 'category'], how='left')

# Convert merged numeric columns to float
df['avg_amount'] = pd.to_numeric(df['avg_amount'], errors='coerce')
df['std_amount'] = pd.to_numeric(df['std_amount'], errors='coerce')
df['expense_count'] = pd.to_numeric(df['expense_count'], errors='coerce')

# Fill NaN values with defaults
df['avg_amount'] = df['avg_amount'].fillna(df['amount'])
df['std_amount'] = df['std_amount'].fillna(1.0)
df['expense_count'] = df['expense_count'].fillna(1)

# Calculate deviation from user's average for this category
df['amount_deviation'] = (df['amount'] - df['avg_amount']) / (df['std_amount'] + 1)

# Calculate monthly spending for user
monthly_spending = df.groupby(['user_id', 'year', 'month'])['amount'].sum().reset_index()
monthly_spending.columns = ['user_id', 'year', 'month', 'monthly_total']
df = df.merge(monthly_spending, on=['user_id', 'year', 'month'], how='left')

# Convert monthly_total to float
df['monthly_total'] = pd.to_numeric(df['monthly_total'], errors='coerce').fillna(df['amount'])

# Calculate percentage of monthly budget
df['pct_of_monthly'] = (df['amount'] / df['monthly_total']) * 100

print(f"✓ Features engineered:")
print(f"  - amount_deviation: deviation from user's category average")
print(f"  - pct_of_monthly: percentage of monthly spending")
print(f"  - expense_count: frequency of expenses in this category")

# Encode categorical features
print("\n[5/7] Encoding categorical features...")

category_encoder = LabelEncoder()
df['category_encoded'] = category_encoder.fit_transform(df['category'])

# Select features for training
feature_columns = [
    'amount',
    'category_encoded',
    'month',
    'day_of_week',
    'amount_deviation',
    'pct_of_monthly',
    'expense_count'
]

X = df[feature_columns].copy()

# Handle any remaining NaN values
X = X.fillna(0)

# Scale features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

print(f"✓ Features encoded and scaled")
print(f"  - Feature columns: {feature_columns}")
print(f"  - Training samples: {len(X_scaled)}")

# Train Isolation Forest model
print("\n[6/7] Training Isolation Forest model...")

# Isolation Forest parameters
# contamination: expected proportion of outliers (5% is reasonable)
# n_estimators: number of trees
# max_samples: number of samples to draw for each tree
# random_state: for reproducibility

model = IsolationForest(
    contamination=0.05,  # Expect 5% of expenses to be anomalies
    n_estimators=100,
    max_samples='auto',
    random_state=42,
    n_jobs=-1  # Use all CPU cores
)

model.fit(X_scaled)

# Predict on training data to see distribution
predictions = model.predict(X_scaled)
anomaly_scores = model.score_samples(X_scaled)

n_anomalies = (predictions == -1).sum()
n_normal = (predictions == 1).sum()

print(f"✓ Model trained successfully")
print(f"  - Algorithm: Isolation Forest")
print(f"  - Contamination rate: 5%")
print(f"  - Estimators: 100")
print(f"  - Training results:")
print(f"    • Normal expenses: {n_normal} ({n_normal/len(predictions)*100:.1f}%)")
print(f"    • Anomalies detected: {n_anomalies} ({n_anomalies/len(predictions)*100:.1f}%)")

# Save model and encoders
print("\n[7/7] Saving model files...")

try:
    # Save model
    joblib.dump(model, 'models/anomaly_detection_model.pkl')
    print("✓ Saved: models/anomaly_detection_model.pkl")
    
    # Save scaler
    joblib.dump(scaler, 'models/anomaly_scaler.pkl')
    print("✓ Saved: models/anomaly_scaler.pkl")
    
    # Save category encoder
    joblib.dump(category_encoder, 'models/anomaly_category_encoder.pkl')
    print("✓ Saved: models/anomaly_category_encoder.pkl")
    
    # Save metadata
    metadata = {
        'model_type': 'IsolationForest',
        'training_date': datetime.now().isoformat(),
        'training_samples': len(df),
        'n_users': int(df['user_id'].nunique()),
        'n_categories': int(df['category'].nunique()),
        'categories': category_encoder.classes_.tolist(),
        'feature_columns': feature_columns,
        'contamination': 0.05,
        'n_estimators': 100,
        'anomalies_detected': int(n_anomalies),
        'normal_expenses': int(n_normal),
        'date_range': {
            'start': str(df['date'].min()),
            'end': str(df['date'].max())
        }
    }
    
    with open('models/anomaly_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    print("✓ Saved: models/anomaly_metadata.json")
    
except Exception as e:
    print(f"✗ Failed to save model files: {e}")
    exit(1)

# Display sample anomalies
print("\n" + "=" * 60)
print("SAMPLE ANOMALIES DETECTED IN TRAINING DATA")
print("=" * 60)

df['anomaly_prediction'] = predictions
df['anomaly_score'] = anomaly_scores

anomalies = df[df['anomaly_prediction'] == -1].sort_values('anomaly_score').head(10)

if len(anomalies) > 0:
    print(f"\nTop 10 most unusual expenses:")
    for idx, row in anomalies.iterrows():
        print(f"\n  User {row['user_id']} - {row['category']}")
        print(f"  Amount: ₹{row['amount']:.2f}")
        print(f"  Date: {row['date']}")
        print(f"  Deviation: {row['amount_deviation']:.2f}x from average")
        print(f"  Anomaly Score: {row['anomaly_score']:.4f}")
else:
    print("\nNo anomalies detected in training data")

print("\n" + "=" * 60)
print("TRAINING COMPLETE ✓")
print("=" * 60)
print("\nModel files saved in 'models/' directory")
print("Ready to use for anomaly detection API")
print("\nNext steps:")
print("1. Start ML service: python ml_anomaly_service.py")
print("2. Test endpoint: POST http://localhost:8001/ml/detect-anomaly")
print("=" * 60)
