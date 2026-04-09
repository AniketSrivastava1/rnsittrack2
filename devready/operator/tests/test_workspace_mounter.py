import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from devready.operator.workspace_mounter import WorkspaceMounter

def test_path_handling():
    # Property 8: Platform Compatibility (Windows paths)
    mounter = WorkspaceMounter()
    path = "C:\\projects\\my_app" if os.name == 'nt' else "/c/projects/my_app"
    formatted = mounter.format_path_for_docker(path)
    assert '\\' not in formatted

def test_mount_validation(tmp_path):
    mounter = WorkspaceMounter()
    
    # Check valid directory
    mounts = mounter.mount_workspace(str(tmp_path))
    assert len(mounts) == 1
    assert mounts[0][1] == "/workspace"
    assert mounts[0][2] == "rw"
    
    # Check non-existent directory
    with pytest.raises(ValueError, match="does not exist"):
        mounter.mount_workspace(str(tmp_path / "nonexistent"))
