"""
Test script for ML Prediction Service
"""

import requests
import json
from datetime import datetime, timedelta

# ML Service URL
ML_SERVICE_URL = "http://localhost:8001"

def test_health():
    """Test health endpoint"""
    print("\n=== Testing Health Endpoint ===")
    try:
        response = requests.get(f"{ML_SERVICE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_model_info():
    """Test model info endpoint"""
    print("\n=== Testing Model Info Endpoint ===")
    try:
        response = requests.get(f"{ML_SERVICE_URL}/model/info")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_ml_prediction():
    """Test ML prediction endpoint"""
    print("\n=== Testing ML Prediction Endpoint ===")
    
    # Sample expense data
    today = datetime.now()
    expenses = []
    
    # Generate sample expenses for last 6 months
    categories = ["Food", "Shopping", "Transport", "Entertainment", "Bills"]
    
    for i in range(6):
        month_date = today - timedelta(days=30 * i)
        for category in categories:
            expenses.append({
                "amount": 500 + (i * 50) + (categories.index(category) * 100),
                "category": category,
                "date": month_date.strftime("%Y-%m-%d")
            })
    
    request_data = {
        "user_id": 2,
        "expenses": expenses
    }
    
    try:
        response = requests.post(
            f"{ML_SERVICE_URL}/ml/predict",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✓ Prediction successful!")
            print(f"  User ID: {result['user_id']}")
            print(f"  Prediction Month: {result['prediction_month']}")
            print(f"  Total Predicted: ₹{result['total_predicted_expense']:.2f}")
            print(f"  Confidence: {result['prediction_confidence']}")
            print(f"\n  Category Predictions:")
            for cat_pred in result['category_predictions']:
                print(f"    - {cat_pred['category']}: ₹{cat_pred['predicted_amount']:.2f} ({cat_pred['confidence']} confidence)")
            print(f"\n  Metrics:")
            for key, value in result['metrics'].items():
                print(f"    - {key}: {value}")
        else:
            print(f"❌ Error: {response.text}")
        
        return response.status_code == 200
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("ML SERVICE TEST SUITE")
    print("=" * 60)
    
    print("\nMake sure the ML service is running on port 8001")
    print("Run: python ml_prediction_service.py")
    
    input("\nPress Enter to start tests...")
    
    results = {
        "Health Check": test_health(),
        "Model Info": test_model_info(),
        "ML Prediction": test_ml_prediction()
    }
    
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 60)

if __name__ == "__main__":
    main()
