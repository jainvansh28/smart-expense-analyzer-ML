"""
Setup Checker for ML Service
Verifies all requirements are met before training
"""

import sys
import os

def check_python_version():
    """Check Python version"""
    print("Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"  ✓ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"  ✗ Python {version.major}.{version.minor} (need 3.8+)")
        return False

def check_dependencies():
    """Check if required packages are installed"""
    print("\nChecking dependencies...")
    required = [
        'fastapi',
        'uvicorn',
        'sklearn',
        'pandas',
        'numpy',
        'pydantic',
        'joblib',
        'mysql.connector'
    ]
    
    missing = []
    for package in required:
        try:
            if package == 'sklearn':
                __import__('sklearn')
            elif package == 'mysql.connector':
                __import__('mysql.connector')
            else:
                __import__(package)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} (missing)")
            missing.append(package)
    
    if missing:
        print(f"\n  Install missing packages:")
        print(f"  pip install -r requirements.txt")
        return False
    return True

def check_database_config():
    """Check database configuration"""
    print("\nChecking database configuration...")
    try:
        from config import DB_CONFIG
        print(f"  ✓ Host: {DB_CONFIG['host']}")
        print(f"  ✓ Database: {DB_CONFIG['database']}")
        print(f"  ✓ User: {DB_CONFIG['user']}")
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def check_database_connection():
    """Check database connection"""
    print("\nChecking database connection...")
    try:
        import mysql.connector
        from config import DB_CONFIG
        
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM expenses")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        print(f"  ✓ Connected successfully")
        print(f"  ✓ Found {count} expense records")
        
        if count < 50:
            print(f"  ⚠ Warning: Only {count} records (recommend 100+)")
        
        return True
    except Exception as e:
        print(f"  ✗ Connection failed: {e}")
        print(f"  Make sure MySQL is running and credentials are correct")
        return False

def check_models_directory():
    """Check if models directory exists"""
    print("\nChecking models directory...")
    if os.path.exists('models'):
        print(f"  ✓ models/ directory exists")
        
        # Check for existing model files
        model_files = ['expense_prediction_model.pkl', 'category_encoder.pkl', 'model_metadata.json']
        for file in model_files:
            path = os.path.join('models', file)
            if os.path.exists(path):
                print(f"  ✓ {file} found")
            else:
                print(f"  ℹ {file} not found (will be created during training)")
        return True
    else:
        print(f"  ℹ models/ directory will be created during training")
        return True

def main():
    """Run all checks"""
    print("=" * 60)
    print("ML SERVICE SETUP CHECKER")
    print("=" * 60)
    
    checks = {
        "Python Version": check_python_version(),
        "Dependencies": check_dependencies(),
        "Database Config": check_database_config(),
        "Database Connection": check_database_connection(),
        "Models Directory": check_models_directory()
    }
    
    print("\n" + "=" * 60)
    print("SETUP STATUS")
    print("=" * 60)
    
    for check_name, passed in checks.items():
        status = "✓ READY" if passed else "✗ FAILED"
        print(f"{check_name}: {status}")
    
    all_passed = all(checks.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ALL CHECKS PASSED!")
        print("\nYou can now train the model:")
        print("  python train_model.py")
    else:
        print("✗ SOME CHECKS FAILED")
        print("\nPlease fix the issues above before training")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
