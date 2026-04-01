"""
Test script for ML Budget Recommendation Service
"""

import requests
import json

BASE_URL = "http://localhost:8003"

print("=" * 60)
print("ML BUDGET RECOMMENDATION SERVICE - TEST SCRIPT")
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
    response = requests.get(f"{BASE_URL}/ml/budget-info")
    if response.status_code == 200:
        info = response.json()
        print(f"Model Type: {info['model_type']}")
        print(f"Training Date: {info['training_date']}")
        print(f"Training Samples: {info['training_samples']}")
        print(f"Users: {info['n_users']}")
        print(f"Categories: {info['n_categories']}")
        print(f"Test Score: {info['test_score']:.4f}")
        print("\nTop 5 Important Features:")
        for feat in info['feature_importance']:
            print(f"  {feat['feature']}: {feat['importance']:.4f}")
        print("✓ Model info retrieved")
    else:
        print(f"✗ Failed to get model info: {response.status_code}")
        print("Note: Make sure you've trained the model first!")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 3: Get budget recommendations for user 1
print("\n[TEST 3] Get Budget Recommendations for User 1")
print("-" * 60)
test_data = {
    "user_id": 1
}
print(f"Request: {json.dumps(test_data, indent=2)}")

try:
    response = requests.post(
        f"{BASE_URL}/ml/budget-recommendation",
        json=test_data,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✓ Success!")
        print(f"\nUser ID: {result['user_id']}")
        print(f"Monthly Income: ₹{result['monthly_income']:.2f}")
        print(f"Total Recommended Budget: ₹{result['total_recommended']:.2f}")
        print(f"Model Confidence: {result['model_confidence']}")
        
        print(f"\nRecommended Budgets:")
        print("-" * 60)
        for budget in result['recommended_budgets']:
            print(f"  {budget['category']:15} | Recommended: ₹{budget['recommended_budget']:8.2f} | Historical Avg: ₹{budget['historical_avg']:8.2f} | Consistency: {budget['consistency_score']:.2f}")
        
        print(f"\nInsight:")
        print(f"  {result['insight']}")
        
        print("\n✓ Budget recommendation test passed")
    else:
        print(f"✗ Request failed: {response.status_code}")
        print(f"Response: {response.text}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 4: Get budget recommendations for user 2
print("\n[TEST 4] Get Budget Recommendations for User 2")
print("-" * 60)
test_data = {
    "user_id": 2
}

try:
    response = requests.post(
        f"{BASE_URL}/ml/budget-recommendation",
        json=test_data,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ User 2 recommendations generated")
        print(f"  Categories: {len(result['recommended_budgets'])}")
        print(f"  Total Budget: ₹{result['total_recommended']:.2f}")
        print(f"  Confidence: {result['model_confidence']}")
    else:
        print(f"⚠ User 2 request: {response.status_code}")
        if response.status_code == 404:
            print("  (No expense history found - this is expected for new users)")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 5: Test with non-existent user
print("\n[TEST 5] Test with Non-Existent User")
print("-" * 60)
test_data = {
    "user_id": 99999
}

try:
    response = requests.post(
        f"{BASE_URL}/ml/budget-recommendation",
        json=test_data,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 404:
        print("✓ Correctly returns 404 for non-existent user")
    else:
        print(f"⚠ Unexpected status code: {response.status_code}")
except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "=" * 60)
print("TESTING COMPLETE")
print("=" * 60)
print("\nIf all tests passed, the ML budget recommendation service is working correctly!")
print("You can now integrate it with the Spring Boot backend.")
print("=" * 60)
