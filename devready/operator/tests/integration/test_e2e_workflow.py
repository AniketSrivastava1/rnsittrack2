import sys
import os
import pytest

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(base_dir))

from operator.tests.setup_test_scenario import TestScenarioManager
from operator.hook_manager import HookManager
from operator.dry_run_executor import DryRunExecutor
from operator.fix_applicator import FixApplicator
from operator.rollback_manager import RollbackManager

class TestDevReadyE2E:
    @pytest.fixture(scope="class")
    def test_bed(self):
        manager = TestScenarioManager()
        project_dir = manager.setup()
        yield project_dir
        manager.teardown()

    def test_hook_installation(self, test_bed):
        hm = HookManager(test_bed)
        assert hm.install_pre_commit_hook() is True

    def test_dry_run_executor(self, test_bed):
        dre = DryRunExecutor()
        fixes = [{"command": ["npm", "install", "lodash"]}]
        results = dre.execute_dry_run(fixes)
        assert len(results) == 1
        assert results[0]["sandbox_success"] is True

    def test_apply_and_rollback(self, test_bed):
        app = FixApplicator()
        app.apply_fix(["npm", "init", "-y"], "local", test_bed)
        
        rm = RollbackManager(test_bed)
        mise_path = os.path.join(test_bed, ".mise.toml")
        snap_id = rm.create_snapshot("global", [mise_path])
        
        with open(mise_path, 'w') as f:
            f.write("corrupted")
            
        assert rm.restore_snapshot(snap_id) is True
        
        with open(mise_path, 'r') as f:
            content = f.read()
        assert "corrupted" not in content
