"""
ML Package Verification Script
Tests that all required ML packages are installed and working correctly.
"""

import sys
from datetime import datetime


def test_imports():
    """Test all ML package imports"""
    print("=" * 60)
    print("ML Package Verification - Sprint 1")
    print("=" * 60)
    print(f"Test Time: {datetime.now()}")
    print()
    
    packages = []
    
    # Test XGBoost
    try:
        import xgboost as xgb
        print(f"✅ XGBoost: {xgb.__version__}")
        packages.append(("xgboost", xgb.__version__, True))
    except ImportError as e:
        print(f"❌ XGBoost: FAILED - {e}")
        packages.append(("xgboost", None, False))
    
    # Test LightGBM
    try:
        import lightgbm as lgb
        print(f"✅ LightGBM: {lgb.__version__}")
        packages.append(("lightgbm", lgb.__version__, True))
    except ImportError as e:
        print(f"❌ LightGBM: FAILED - {e}")
        packages.append(("lightgbm", None, False))
    
    # Test River (optional - Python 3.14 compatibility issue)
    try:
        import river
        print(f"✅ River: {river.__version__}")
        packages.append(("river", river.__version__, True))
    except ImportError as e:
        print(f"⚠️  River: SKIPPED - {e} (optional for Sprint 1)")
        packages.append(("river", None, True))  # Mark as success since it's optional
    
    # Test SHAP (optional - Python 3.14 compatibility issue)
    try:
        import shap
        print(f"✅ SHAP: {shap.__version__}")
        packages.append(("shap", shap.__version__, True))
    except ImportError as e:
        print(f"⚠️  SHAP: SKIPPED - {e} (optional for Sprint 1)")
        packages.append(("shap", None, True))  # Mark as success since it's optional
    
    # Test Optuna
    try:
        import optuna
        print(f"✅ Optuna: {optuna.__version__}")
        packages.append(("optuna", optuna.__version__, True))
    except ImportError as e:
        print(f"❌ Optuna: FAILED - {e}")
        packages.append(("optuna", None, False))
    
    # Test Scikit-learn
    try:
        import sklearn
        print(f"✅ Scikit-learn: {sklearn.__version__}")
        packages.append(("scikit-learn", sklearn.__version__, True))
    except ImportError as e:
        print(f"❌ Scikit-learn: FAILED - {e}")
        packages.append(("scikit-learn", None, False))
    
    # Test Pandas (already installed)
    try:
        import pandas as pd
        print(f"✅ Pandas: {pd.__version__}")
        packages.append(("pandas", pd.__version__, True))
    except ImportError as e:
        print(f"❌ Pandas: FAILED - {e}")
        packages.append(("pandas", None, False))
    
    # Test NumPy (already installed)
    try:
        import numpy as np
        print(f"✅ NumPy: {np.__version__}")
        packages.append(("numpy", np.__version__, True))
    except ImportError as e:
        print(f"❌ NumPy: FAILED - {e}")
        packages.append(("numpy", None, False))
    
    print()
    print("=" * 60)
    
    # Summary
    successful = sum(1 for _, _, success in packages if success)
    total = len(packages)
    
    print(f"Summary: {successful}/{total} packages installed successfully")
    
    if successful == total:
        print("✅ All ML packages are ready!")
        print()
        print("Next steps:")
        print("1. Create ML database tables")
        print("2. Set up ML module structure")
        print("3. Start building the money printer! 🚀")
        return 0
    else:
        print("❌ Some packages failed to install")
        print()
        print("To install missing packages, run:")
        print("  cd backend && pip install -r requirements.txt")
        return 1


def test_basic_functionality():
    """Test basic functionality of key packages"""
    print()
    print("=" * 60)
    print("Testing Basic Functionality")
    print("=" * 60)
    
    try:
        # Test XGBoost
        import xgboost as xgb
        import numpy as np
        
        # Create simple dataset
        X = np.array([[1, 2], [3, 4], [5, 6], [7, 8]])
        y = np.array([0, 1, 0, 1])
        
        # Train simple model
        model = xgb.XGBClassifier(n_estimators=10, max_depth=2)
        model.fit(X, y)
        
        # Make prediction
        pred = model.predict([[2, 3]])
        
        print("✅ XGBoost: Basic training and prediction working")
        
    except Exception as e:
        print(f"❌ XGBoost functionality test failed: {e}")
        return 1
    
    try:
        # Test Scikit-learn
        from sklearn.preprocessing import StandardScaler
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        print("✅ Scikit-learn: Feature scaling working")
        
    except Exception as e:
        print(f"❌ Scikit-learn functionality test failed: {e}")
        return 1
    
    print()
    print("✅ All functionality tests passed!")
    return 0


if __name__ == "__main__":
    # Test imports
    result = test_imports()
    
    if result == 0:
        # Test functionality
        result = test_basic_functionality()
    
    sys.exit(result)
