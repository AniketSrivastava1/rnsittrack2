import os
import logging
import stat
from git import Repo, InvalidGitRepositoryError

logger = logging.getLogger(__name__)

class HookManager:
    def __init__(self, project_root: str):
        self.project_root = project_root
        try:
            self.repo = Repo(project_root)
            self.git_dir = self.repo.git_dir
        except InvalidGitRepositoryError:
            self.repo = None
            self.git_dir = None
            logger.error(f"'{project_root}' is not a valid git repository")

    def _install_hook(self, hook_name: str, script_content: str) -> bool:
        if not self.git_dir:
            return False
            
        hooks_dir = os.path.join(self.git_dir, "hooks")
        os.makedirs(hooks_dir, exist_ok=True)
        hook_path = os.path.join(hooks_dir, hook_name)
        
        existing_content = ""
        if os.path.exists(hook_path):
            with open(hook_path, 'r', encoding='utf-8') as f:
                existing_content = f.read()
                
            if "# DevReady Hook" in existing_content:
                logger.debug(f"{hook_name} already installed.")
                return True
                
        new_content = "#!/bin/sh\n\n"
        if existing_content:
            lines = existing_content.split('\n')
            if lines and lines[0].startswith('#!'):
                lines = lines[1:]
            new_content += "\n".join(lines) + "\n\n"
            
        new_content += "# DevReady Hook\n"
        new_content += script_content + "\n"
        
        try:
            with open(hook_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            st = os.stat(hook_path)
            os.chmod(hook_path, st.st_mode | stat.S_IEXEC)
            logger.info(f"Installed {hook_name} hook.")
            return True
        except Exception as e:
            logger.error(f"Failed to install {hook_name}: {e}")
            return False

    def install_post_merge_hook(self) -> bool:
        script = 'devready scan --quick || true'
        return self._install_hook("post-merge", script)
        
    def install_post_checkout_hook(self) -> bool:
        script = 'devready scan --quick || true' 
        return self._install_hook("post-checkout", script)

    def install_pre_commit_hook(self) -> bool:
        script = 'devready validate || exit 1'
        return self._install_hook("pre-commit", script)
