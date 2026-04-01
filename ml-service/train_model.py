"""
ML Model Training Script for Smart Expense Analyzer
Trains a global expense prediction model using all users' historical data
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import mysql.connector
from datetime import datetime
import os
import json
from config import DB_CONFIG

# Model configuration
MODEL_PATH = 'models/expense_prediction_model.pkl'
ENCODERS_PATH = 'models/category_encoder.pkl'
METADATA_PATH = 'models/model_metadata.json'

def create_models_directory():
    """Create models directory if it doesn't exist"""
    os.makedirs('models', exist_ok=True)
    print("✓ Models directory ready")

def fetch_training_data():
    """Fetch all expense data from MySQL database"""
    print("\n=== Fetching Training Data from Database ===")
    
    # Debug: Print DB config (hide password for security)
    debug_config = DB_CONFIG.copy()
    debug_config['password'] = '***' + DB_CONFIG['password'][-3:] if len(DB_CONFIG['password']) > 3 else '***'
    print(f"Database Config: {debug_config}")
    
    try:
        print("Attempting to connect to MySQL...")
        conn = mysql.connector.connect(**DB_CONFIG)
        print("✓ Connected to database successfully")
        cursor = conn.cursor(dictionary=True)
        
        # Fetch all expenses
        query = """
        SELECT 
            user_id,
            amount,
            category,
            date,
            YEAR(date) as year,
            MONTH(date) as month
        FROM expenses
        ORDER BY user_id, date
        """
        
        cursor.execute(query)
        expenses = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        df = pd.DataFrame(expenses)
        print(f"✓ Fetched {len(df)} expense records")
        print(f"✓ Users: {df['user_id'].nunique()}")
        print(f"✓ Categories: {df['category'].nunique()}")
        print(f"✓ Date range: {df['date'].min()} to {df['date'].max()}")
        
        return df
    
    except Exception as e:
        print(f"✗ Error fetching data: {e}")
        raise

def prepare_features(df):
    """Prepare features for ML model"""
    print("\n=== Preparing Features ===")
    
    # Create year-month column
    df['year_month'] = df['year'].astype(str) + '-' + df['month'].astype(str).str.zfill(2)
    
    # Aggregate data by user, year, month, and category
    monthly_category_data = df.groupby(['user_id', 'year', 'month', 'category']).agg({
        'amount': 'sum'
    }).reset_index()
    
    # Calculate total monthly spending per user
    monthly_totals = df.groupby(['user_id', 'year', 'month']).agg({
        'amount': 'sum'
    }).reset_index()
    monthly_totals.rename(columns={'amount': 'total_monthly_spending'}, inplace=True)
    
    # Merge category spending with monthly totals
    features_df = monthly_category_data.merge(
        monthly_totals,
        on=['user_id', 'year', 'month'],
        how='left'
    )
    
    # Calculate category percentage
    features_df['category_percentage'] = (
        features_df['amount'] / features_df['total_monthly_spending'] * 100
    )
    
    # Encode categorical features
    category_encoder = LabelEncoder()
    features_df['category_encoded'] = category_encoder.fit_transform(features_df['category'])
    
    # Create time-based features
    features_df['month_sin'] = np.sin(2 * np.pi * features_df['month'] / 12)
    features_df['month_cos'] = np.cos(2 * np.pi * features_df['month'] / 12)
    
    # Calculate rolling averages (last 3 months)
    features_df = features_df.sort_values(['user_id', 'year', 'month'])
    features_df['rolling_avg_3m'] = features_df.groupby(['user_id', 'category'])['amount'].transform(
        lambda x: x.rolling(window=3, min_periods=1).mean()
    )
    
    print(f"✓ Prepared {len(features_df)} feature rows")
    print(f"✓ Features: user_id, year, month, category, total_monthly_spending, etc.")
    
    return features_df, category_encoder

def create_prediction_dataset(features_df):
    """Create dataset for next month prediction"""
    print("\n=== Creating Prediction Dataset ===")
    
    # For each user-category combination, predict next month spending
    # Target: amount (spending for that category in that month)
    
    # Features for prediction
    feature_columns = [
        'user_id',
        'month',
        'category_encoded',
        'month_sin',
        'month_cos',
        'rolling_avg_3m',
        'category_percentage'
    ]
    
    X = features_df[feature_columns]
    y = features_df['amount']
    
    print(f"✓ Feature matrix shape: {X.shape}")
    print(f"✓ Target vector shape: {y.shape}")
    
    return X, y, feature_columns

def train_model(X, y):
    """Train Linear Regression model"""
    print("\n=== Training Model ===")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    print(f"✓ Training set: {len(X_train)} samples")
    print(f"✓ Test set: {len(X_test)} samples")
    
    # Train model
    model = LinearRegression()
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)
    
    train_mae = mean_absolute_error(y_train, y_pred_train)
    test_mae = mean_absolute_error(y_test, y_pred_test)
    train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
    test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
    train_r2 = r2_score(y_train, y_pred_train)
    test_r2 = r2_score(y_test, y_pred_test)
    
    print("\n=== Model Performance ===")
    print(f"Training MAE: ₹{train_mae:.2f}")
    print(f"Test MAE: ₹{test_mae:.2f}")
    print(f"Training RMSE: ₹{train_rmse:.2f}")
    print(f"Test RMSE: ₹{test_rmse:.2f}")
    print(f"Training R²: {train_r2:.4f}")
    print(f"Test R²: {test_r2:.4f}")
    
    return model, {
        'train_mae': float(train_mae),
        'test_mae': float(test_mae),
        'train_rmse': float(train_rmse),
        'test_rmse': float(test_rmse),
        'train_r2': float(train_r2),
        'test_r2': float(test_r2),
        'train_samples': len(X_train),
        'test_samples': len(X_test)
    }

def save_model(model, category_encoder, feature_columns, metrics):
    """Save trained model and metadata"""
    print("\n=== Saving Model ===")
    
    # Save model
    joblib.dump(model, MODEL_PATH)
    print(f"✓ Model saved to {MODEL_PATH}")
    
    # Save encoder
    joblib.dump(category_encoder, ENCODERS_PATH)
    print(f"✓ Encoder saved to {ENCODERS_PATH}")
    
    # Save metadata
    metadata = {
        'trained_at': datetime.now().isoformat(),
        'model_type': 'LinearRegression',
        'feature_columns': feature_columns,
        'metrics': metrics,
        'version': '1.0'
    }
    
    with open(METADATA_PATH, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"✓ Metadata saved to {METADATA_PATH}")

def main():
    """Main training pipeline"""
    print("=" * 60)
    print("ML MODEL TRAINING - Smart Expense Analyzer")
    print("=" * 60)
    
    try:
        # Step 1: Create models directory
        create_models_directory()
        
        # Step 2: Fetch data
        df = fetch_training_data()
        
        if len(df) == 0:
            print("✗ No data available for training")
            return
        
        # Step 3: Prepare features
        features_df, category_encoder = prepare_features(df)
        
        # Step 4: Create prediction dataset
        X, y, feature_columns = create_prediction_dataset(features_df)
        
        # Step 5: Train model
        model, metrics = train_model(X, y)
        
        # Step 6: Save model
        save_model(model, category_encoder, feature_columns, metrics)
        
        print("\n" + "=" * 60)
        print("✓ TRAINING COMPLETE!")
        print("=" * 60)
        print(f"\nModel files created:")
        print(f"  - {MODEL_PATH}")
        print(f"  - {ENCODERS_PATH}")
        print(f"  - {METADATA_PATH}")
        print("\nYou can now use the ML prediction API!")
        
    except Exception as e:
        print(f"\n✗ Training failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
