# ML Service - Smart Expense Analyzer

## Overview
This ML service provides machine learning-based expense predictions using a trained Linear Regression model. It runs **separately** from the existing rule-based prediction system.

## Architecture

### Two Prediction Systems (Parallel)
1. **Rule-Based System** (Port 8000) - `main.py`
   - Simple statistical predictions
   - No training required
   - Always available

2. **ML-Based System** (Port 8001) - `ml_prediction_service.py`
   - Trained on global multi-user dataset
   - Requires model training first
   - More accurate predictions

## Dataset
- **User 1**: 507 expenses
- **User 2**: 599 expenses
- **User 3**: 481 expenses
- **Total**: 1,587+ expense records

## Setup

### 1. Install Dependencies
```bash
cd ml-service
pip install -r requirements.txt
```

### 2. Configure Database
Edit `config.py` or set environment variables:
```bash
export DB_HOST=localhost
export DB_USER=root
export DB_PASSWORD=root
export DB_NAME=expense_analyzer
```

### 3. Train the Model
```bash
python train_model.py
```

This will:
- Fetch all expense data from MySQL
- Prepare features (user_id, month, category, rolling averages, etc.)
- Train Linear Regression model
- Save model files to `models/` directory
- Display training metrics

Expected output:
```
=== Model Performance ===
Training MAE: ₹XXX.XX
Test MAE: ₹XXX.XX
Training R²: 0.XXXX
Test R²: 0.XXXX
```

### 4. Start ML Service
```bash
python ml_prediction_service.py
```

Service will run on: `http://localhost:8001`

### 5. (Optional) Start Rule-Based Service
```bash
python main.py
```

Service will run on: `http://localhost:8000`

## API Endpoints

### ML Service (Port 8001)

#### 1. Health Check
```
GET http://localhost:8001/health
```

#### 2. Model Info
```
GET http://localhost:8001/model/info
```

Response:
```json
{
  "model_type": "LinearRegression",
  "trained_at": "2026-03-08T13:30:00",
  "version": "1.0",
  "metrics": {
    "test_mae": 250.50,
    "test_r2": 0.85
  }
}
```

#### 3. ML Prediction
```
POST http://localhost:8001/ml/predict
```

Request:
```json
{
  "user_id": 2,
  "expenses": [
    {
      "amount": 500.00,
      "category": "Food",
      "date": "2026-01-15"
    },
    {
      "amount": 1200.00,
      "category": "Shopping",
      "date": "2026-01-20"
    }
  ],
  "target_month": 2,
  "target_year": 2026
}
```

Response:
```json
{
  "user_id": 2,
  "prediction_month": "2026-02",
  "total_predicted_expense": 3500.50,
  "category_predictions": [
    {
      "category": "Food",
      "predicted_amount": 550.25,
      "confidence": "High"
    },
    {
      "category": "Shopping",
      "predicted_amount": 1300.00,
      "confidence": "Medium"
    }
  ],
  "model_version": "1.0",
  "prediction_confidence": "High",
  "metrics": {
    "categories_predicted": 5,
    "historical_months": 6,
    "total_expenses_analyzed": 54
  }
}
```

## Model Features

### Input Features
1. `user_id` - User identifier
2. `month` - Target month (1-12)
3. `category_encoded` - Encoded category
4. `month_sin` - Sine of month (seasonal pattern)
5. `month_cos` - Cosine of month (seasonal pattern)
6. `rolling_avg_3m` - 3-month rolling average
7. `category_percentage` - Category spending percentage

### Target
- `amount` - Predicted expense amount for category

## Model Files

After training, these files are created in `models/`:

1. `expense_prediction_model.pkl` - Trained Linear Regression model
2. `category_encoder.pkl` - Label encoder for categories
3. `model_metadata.json` - Model metadata and metrics

## Retraining

To retrain the model with new data:

```bash
python train_model.py
```

The ML service will automatically reload the new model on next request.

## Comparison: Rule-Based vs ML-Based

| Feature | Rule-Based | ML-Based |
|---------|-----------|----------|
| Port | 8000 | 8001 |
| Training Required | No | Yes |
| Accuracy | Basic | Higher |
| Data Required | User's own | Global dataset |
| Prediction Method | Statistical average | Linear Regression |
| Category-wise | No | Yes |
| Confidence Score | No | Yes |

## Integration with Backend

The Java backend can call either service:

### Rule-Based (Existing)
```java
// MLServiceClient.java already configured for port 8000
```

### ML-Based (New)
```java
// Create new client for port 8001
String mlUrl = "http://localhost:8001/ml/predict";
// Send request with user expenses
```

## Troubleshooting

### Model Not Found
```
⚠ Model not found. Please run train_model.py first.
```
**Solution**: Run `python train_model.py`

### Database Connection Error
```
✗ Error fetching data: Access denied for user
```
**Solution**: Check `config.py` database credentials

### Low Accuracy
```
Test R²: 0.30
```
**Solution**: 
- Add more training data
- Try different algorithms (Random Forest, XGBoost)
- Feature engineering

## Future Enhancements

1. **Advanced Models**
   - Random Forest
   - XGBoost
   - Neural Networks (LSTM for time series)

2. **More Features**
   - Day of week patterns
   - Holiday effects
   - Income data
   - User demographics

3. **Automated Retraining**
   - Scheduled retraining (weekly/monthly)
   - Trigger on new data threshold

4. **Model Versioning**
   - A/B testing
   - Model comparison
   - Rollback capability

## Performance Metrics

Expected performance on current dataset:
- **MAE**: ₹200-400 (Mean Absolute Error)
- **RMSE**: ₹300-500 (Root Mean Squared Error)
- **R²**: 0.70-0.85 (Coefficient of Determination)

## License
Part of Smart Expense Analyzer project
