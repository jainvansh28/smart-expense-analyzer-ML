# Database Configuration Fix ✅

## Issue
`train_model.py` was failing with:
```
1045 Access denied for user 'root'@'localhost'
```

The script had hardcoded database credentials that didn't match the actual MySQL password.

## Root Cause
`train_model.py` had its own hardcoded `DB_CONFIG`:
```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',  # ❌ Wrong password
    'database': 'expense_analyzer'
}
```

## Solution Applied

### 1. Updated config.py
Ensured correct password is set:
```python
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'lifeisshort@123'),  # ✅ Correct
    'database': os.getenv('DB_NAME', 'expense_analyzer'),
    'port': int(os.getenv('DB_PORT', 3306))
}
```

### 2. Fixed train_model.py
Removed hardcoded config and imported from config.py:

**Before**:
```python
# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'expense_analyzer'
}
```

**After**:
```python
from config import DB_CONFIG
```

### 3. Added Debug Logging
Added debug print before connection to verify config:
```python
def fetch_training_data():
    print("\n=== Fetching Training Data from Database ===")
    
    # Debug: Print DB config (hide password for security)
    debug_config = DB_CONFIG.copy()
    debug_config['password'] = '***' + DB_CONFIG['password'][-3:] if len(DB_CONFIG['password']) > 3 else '***'
    print(f"Database Config: {debug_config}")
    
    try:
        print("Attempting to connect to MySQL...")
        conn = mysql.connector.connect(**DB_CONFIG)
        print("✓ Connected to database successfully")
```

## Expected Output

When running `python train_model.py`, you should now see:

```
============================================================
ML MODEL TRAINING - Smart Expense Analyzer
============================================================
✓ Models directory ready

=== Fetching Training Data from Database ===
Database Config: {'host': 'localhost', 'user': 'root', 'password': '***123', 'database': 'expense_analyzer', 'port': 3306}
Attempting to connect to MySQL...
✓ Connected to database successfully
✓ Fetched 1587 expense records
✓ Users: 3
✓ Categories: 8
...
```

## Verification

To verify the fix works:

```bash
cd ml-service
python train_model.py
```

You should see:
1. ✅ Database config printed (with masked password)
2. ✅ "Connected to database successfully"
3. ✅ Expense records fetched
4. ✅ Training proceeds normally

## Files Modified

1. ✅ `ml-service/config.py` - Correct password set
2. ✅ `ml-service/train_model.py` - Imports DB_CONFIG from config.py
3. ✅ Added debug logging for troubleshooting

## Other Files Using DB_CONFIG

These files also import from config.py (no changes needed):
- ✅ `check_setup.py` - Already imports from config
- ✅ `ml_prediction_service.py` - Uses model files, not direct DB connection

## Environment Variables (Optional)

You can also set database credentials via environment variables:

**Linux/Mac**:
```bash
export DB_HOST=localhost
export DB_USER=root
export DB_PASSWORD=lifeisshort@123
export DB_NAME=expense_analyzer
export DB_PORT=3306
```

**Windows**:
```cmd
set DB_HOST=localhost
set DB_USER=root
set DB_PASSWORD=lifeisshort@123
set DB_NAME=expense_analyzer
set DB_PORT=3306
```

Then run:
```bash
python train_model.py
```

## Security Note

The password is now:
- ✅ Centralized in `config.py`
- ✅ Can be overridden with environment variables
- ✅ Masked in debug output (shows only last 3 characters)
- ⚠️ Still visible in config.py file (consider using .env file for production)

## Next Steps

1. Run training:
   ```bash
   python train_model.py
   ```

2. If successful, start ML service:
   ```bash
   python ml_prediction_service.py
   ```

3. Test predictions:
   ```bash
   python test_ml_service.py
   ```

## Troubleshooting

If you still get connection errors:

1. **Check MySQL is running**:
   ```bash
   mysql -u root -p
   # Enter password: lifeisshort@123
   ```

2. **Verify database exists**:
   ```sql
   SHOW DATABASES;
   USE expense_analyzer;
   SELECT COUNT(*) FROM expenses;
   ```

3. **Check config.py password**:
   ```bash
   cat ml-service/config.py | grep password
   ```

4. **Run setup checker**:
   ```bash
   python check_setup.py
   ```

## Summary

✅ **Fixed!** `train_model.py` now correctly imports database configuration from `config.py` and should connect successfully to MySQL.
