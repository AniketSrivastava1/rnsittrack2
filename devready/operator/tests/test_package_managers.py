import pytest
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from package_managers.adapter import registry
# Import to register
from package_managers import nodejs, python, other

def test_package_manager_detection(tmp_path):
    pnpm_lock = tmp_path / "pnpm-lock.yaml"
    pnpm_lock.touch()
    
    adapter = registry.detect_package_manager("nodejs", str(tmp_path))
    assert adapter.name == "pnpm"
    assert adapter.generate_fix_command("install", "lodash", "4.17.21") == ["pnpm", "add", "lodash@4.17.21"]
    
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    adapter2 = registry.detect_package_manager("python", str(empty_dir))
    assert adapter2.name == "pip" # default fallback
