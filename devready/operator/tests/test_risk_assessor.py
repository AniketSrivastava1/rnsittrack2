import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from risk_assessor import RiskAssessor

def test_risk_classification():
    # Property 6: Risk Assessment Accuracy
    assessor = RiskAssessor()
    
    # Global systems
    brew_fix = assessor.classify_fix(["brew", "install", "node"])
    assert brew_fix["scope"] == "global"
    assert brew_fix["risk_level"] == "high"
    
    # Version Managers
    nvm_fix = assessor.classify_fix(["nvm", "install", "18"])
    assert nvm_fix["scope"] == "user_global"
    assert nvm_fix["risk_level"] == "medium"
    
    # Local packages
    npm_fix = assessor.classify_fix(["npm", "install", "lodash"])
    assert npm_fix["scope"] == "local"
    assert npm_fix["risk_level"] == "low"
    
    # Global tool installs via local managers
    npm_global = assessor.classify_fix(["npm", "install", "-g", "jest"])
    assert npm_global["scope"] == "global"
    assert npm_global["risk_level"] == "high"
    
    # Isolation recommendations
    assert npm_fix["isolation"] == "sandbox_only"
    assert brew_fix["isolation"] == "snapshot_and_rollback"
