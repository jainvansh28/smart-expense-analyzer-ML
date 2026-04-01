"""
Quick test to verify decimal.Decimal conversion fix
"""

import pandas as pd
from decimal import Decimal

print("Testing decimal.Decimal to float conversion...")
print("=" * 60)

# Simulate MySQL data with Decimal types
test_data = {
    'amount': [Decimal('500.50'), Decimal('1200.00'), Decimal('350.75')],
    'user_id': [1, 2, 1],
    'category': ['Food', 'Travel', 'Food']
}

df = pd.DataFrame(test_data)

print("\n[BEFORE] Data types:")
print(df.dtypes)
print("\nSample data:")
print(df)

# Apply the fix
print("\n[APPLYING FIX] Converting to float...")
numeric_columns = ['amount', 'user_id']
for col in numeric_columns:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

print("\n[AFTER] Data types:")
print(df.dtypes)
print("\nSample data:")
print(df)

# Test mathematical operations
print("\n[TESTING] Mathematical operations...")
try:
    # This would fail with Decimal types
    df['amount_doubled'] = df['amount'] * 2.0
    df['amount_plus_100'] = df['amount'] + 100.0
    
    print("✓ Multiplication works")
    print("✓ Addition works")
    print("\nResult:")
    print(df[['amount', 'amount_doubled', 'amount_plus_100']])
    
    print("\n" + "=" * 60)
    print("✓ FIX VERIFIED - All operations successful!")
    print("=" * 60)
    
except Exception as e:
    print(f"\n✗ ERROR: {e}")
    print("Fix did not work properly")
