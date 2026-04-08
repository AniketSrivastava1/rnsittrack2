import os
import shutil
import tempfile
import subprocess
import logging

logger = logging.getLogger(__name__)

class TestScenarioManager:
    def __init__(self):
        self.fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures", "mock-stack")
        self.temp_dir = None

    def setup(self):
        self.temp_dir = tempfile.mkdtemp(prefix="devready-e2e-")
        logger.info(f"Setting up test bed in {self.temp_dir}")
        shutil.copytree(self.fixtures_dir, self.temp_dir, dirs_exist_ok=True)
        
        subprocess.run(["git", "init"], cwd=self.temp_dir, check=False, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=self.temp_dir, check=False, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.temp_dir, check=False, capture_output=True)
        subprocess.run(["git", "add", "."], cwd=self.temp_dir, check=False, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=self.temp_dir, check=False, capture_output=True)
        
        return self.temp_dir

    def teardown(self):
        if self.temp_dir and os.path.exists(self.temp_dir):
            import stat
            def rmtree_onerror(func, path, exc_info):
                os.chmod(path, stat.S_IWRITE)
                try:
                    func(path)
                except Exception:
                    pass
            shutil.rmtree(self.temp_dir, onerror=rmtree_onerror)
            logger.info(f"Tore down test bed {self.temp_dir}")
