"""
Configuration file for ML Service
"""

import os

# Database Configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'lifeisshort@123'),
    'database': os.getenv('DB_NAME', 'expense_analyzer'),
    'port': int(os.getenv('DB_PORT', 3306))
}

# Model Configuration
MODEL_DIR = 'models'
MODEL_PATH = os.path.join(MODEL_DIR, 'expense_prediction_model.pkl')
ENCODERS_PATH = os.path.join(MODEL_DIR, 'category_encoder.pkl')
METADATA_PATH = os.path.join(MODEL_DIR, 'model_metadata.json')

# Training Configuration
TEST_SIZE = 0.2
RANDOM_STATE = 42
MIN_SAMPLES_FOR_TRAINING = 50

# API Configuration
ML_SERVICE_HOST = os.getenv('ML_SERVICE_HOST', '0.0.0.0')
ML_SERVICE_PORT = int(os.getenv('ML_SERVICE_PORT', 8001))

# Original service (rule-based) runs on port 8000
RULE_BASED_SERVICE_PORT = 8000
