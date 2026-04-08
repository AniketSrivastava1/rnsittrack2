import os
import json
import logging
import time
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class RollbackManager:
    def __init__(self, project_root: str):
        self.project_root = project_root
        self.snapshots_dir = os.path.join(project_root, ".devready", "snapshots")
        try:
            os.makedirs(self.snapshots_dir, exist_ok=True)
        except Exception:
            pass
        self.max_snapshots = 5

    def create_snapshot(self, scope: str, config_files: List[str] = None) -> str:
        """Create a snapshot of current state before a fix."""
        snapshot_id = f"snap_{int(time.time())}"
        snapshot_path = os.path.join(self.snapshots_dir, f"{snapshot_id}.json")
        
        backed_up_configs = {}
        if config_files:
            for fpath in config_files:
                if os.path.exists(fpath):
                    with open(fpath, 'r', encoding='utf-8') as f:
                        backed_up_configs[fpath] = f.read()
                    
        snapshot_data = {
            "id": snapshot_id,
            "timestamp": time.time(),
            "scope": scope,
            "configs": backed_up_configs
        }
        
        with open(snapshot_path, 'w', encoding='utf-8') as f:
            json.dump(snapshot_data, f, indent=2)
            
        logger.info(f"Created rollback snapshot: {snapshot_id}")
        self._cleanup_old_snapshots()
        return snapshot_id

    def restore_snapshot(self, snapshot_id: str) -> bool:
        snapshot_path = os.path.join(self.snapshots_dir, f"{snapshot_id}.json")
        if not os.path.exists(snapshot_path):
            logger.error(f"Snapshot {snapshot_id} not found.")
            return False
            
        try:
            with open(snapshot_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            for fpath, content in data.get("configs", {}).items():
                with open(fpath, 'w', encoding='utf-8') as out:
                    out.write(content)
                    
            logger.info(f"Restored configs from snapshot {snapshot_id}.")
            return True
        except Exception as e:
            logger.error(f"Failed to restore snapshot {snapshot_id}: {e}")
            print(f"\nDevReady Manual Recovery needed for snapshot {snapshot_id}.")
            return False

    def _cleanup_old_snapshots(self):
        try:
            snaps = []
            for f in os.listdir(self.snapshots_dir):
                if f.endswith('.json'):
                    snaps.append(os.path.join(self.snapshots_dir, f))
            snaps.sort(key=os.path.getmtime)
            
            while len(snaps) > self.max_snapshots:
                oldest = snaps.pop(0)
                os.remove(oldest)
        except Exception as e:
            logger.warning(f"Cleanup error: {e}")
