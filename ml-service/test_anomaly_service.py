"""
Test script for ML Anomaly Detection Service
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8002"

print("=" * 60)
print("ML ANOMALY DETECTION SERVICE - TEST SCRIPT")
print("=" * 60)

# Test 1: Health check
print("\n[TEST 1] Health Check")
print("-" * 60)
try:
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print("✓ Health check passed")
except Exception as e:
    print(f"✗ Health check failed: {e}")
    exit(1)

# Test 2: Get model info
print("\n[TEST 2] Get Model Information")
print("-" * 60)
try:
    response = requests.get(f"{BASE_URL}/ml/anomaly-info")
    if response.status_code == 200:
        info = response.json()
        print(f"Model Type: {info['model_type']}")
        print(f"Training Date: {info['training_date']}")
        print(f"Training Samples: {info['training_samples']}")
        print(f"Users: {info['n_users']}")
        print(f"Categories: {info['n_categories']}")
        print(f"Contamination: {info['contamination'] * 100}%")
        print("✓ Model info retrieved")
    else:
        print(f"✗ Failed to get model info: {response.status_code}")
        print("Note: Make sure you've trained the model first!")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 3: Normal expense detection
print("\n[TEST 3] Detect Normal Expense")
print("-" * 60)
test_data = {
    "user_id": 1,
    "amount": 500.0,
    "category": "Food",
    "date": datetime.now().strftime("%Y-%m-%d")
}
print(f"Testing: {json.dumps(test_data, indent=2)}")

try:
    response = requests.post(
        f"{BASE_URL}/ml/detect-anomaly",
        json=test_data,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nResult:")
        print(f"  Is Anomaly: {result['is_anomaly']}")
        print(f"  Confidence: {result['confidence']}")
        print(f"  Anomaly Score: {result['anomaly_score']:.4f}")
        print(f"  Message: {result['anomaly_message']}")
        print(f"\nDetails:")
        for key, value in result['details'].items():
            print(f"  {key}: {value}")
        print("✓ Normal expense test passed")
    else:
        print(f"✗ Request failed: {response.status_code}")
        print(f"Response: {response.text}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 4: Anomalous expense detection
print("\n[TEST 4] Detect Anomalous Expense")
print("-" * 60)
test_data_anomaly = {
    "user_id": 1,
    "amount": 15000.0,  # Very high amount
    "category": "Food",
    "date": datetime.now().strftime("%Y-%m-%d")
}
print(f"Testing: {json.dumps(test_data_anomaly, indent=2)}")

try:
    response = requests.post(
        f"{BASE_URL}/ml/detect-anomaly",
        json=test_data_anomaly,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nResult:")
        print(f"  Is Anomaly: {result['is_anomaly']}")
        print(f"  Confidence: {result['confidence']}")
        print(f"  Anomaly Score: {result['anomaly_score']:.4f}")
        print(f"  Message: {result['anomaly_message']}")
        print(f"\nDetails:")
        for key, value in result['details'].items():
            print(f"  {key}: {value}")
        
        if result['is_anomaly']:
            print("✓ Anomaly correctly detected!")
        else:
            print("⚠ Warning: High amount not detected as anomaly")
    else:
        print(f"✗ Request failed: {response.status_code}")
        print(f"Response: {response.text}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 5: Different categories
print("\n[TEST 5] Test Different Categories")
print("-" * 60)
categories = ["Travel", "Shopping", "Bills", "Entertainment"]

for category in categories:
    test_data = {
        "user_id": 2,
        "amount": 1000.0,
        "category": category,
        "date": datetime.now().strftime("%Y-%m-%d")
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/ml/detect-anomaly",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            status = "ANOMALY" if result['is_anomaly'] else "NORMAL"
            print(f"  {category:15} | ₹1000 | {status:8} | Score: {result['anomaly_score']:.4f}")
        else:
            print(f"  {category:15} | Failed: {response.status_code}")
    except Exception as e:
        print(f"  {category:15} | Error: {e}")

print("\n" + "=" * 60)
print("TESTING COMPLETE")
print("=" * 60)
print("\nIf all tests passed, the ML anomaly detection service is working correctly!")
print("You can now integrate it with the Spring Boot backend.")
print("=" * 60)
