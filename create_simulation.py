import os
import json
import shutil
import subprocess

def create_mock_project():
    project_dir = os.path.expanduser(r"~\devready_cursed_project")
    print(f"Creating cursed mock project at: {project_dir}")
    
    if os.path.exists(project_dir):
        shutil.rmtree(project_dir, ignore_errors=True)
    os.makedirs(project_dir)
    
    # 1. Tooling Conflict
    package_json = {
        "name": "cursed-app",
        "version": "1.0.0",
        "dependencies": {
            "lodash": "^4.17.21"
        },
        "engines": {
            "node": ">=18.0.0"
        }
    }
    with open(os.path.join(project_dir, "package.json"), "w") as f:
        json.dump(package_json, f, indent=2)
        
    with open(os.path.join(project_dir, ".node-version"), "w") as f:
        f.write("14.17.6\n")
        
    # 2. Missing dependencies
    with open(os.path.join(project_dir, "requirements.txt"), "w") as f:
        f.write("requests==2.28.1\nnonexistent-cursed-pkg==1.0\n")
        
    # Initialize basic git
    try:
        subprocess.run(["git", "init"], cwd=project_dir, check=False, stdout=subprocess.DEVNULL)
        subprocess.run(["git", "add", "."], cwd=project_dir, check=False, stdout=subprocess.DEVNULL)
        subprocess.run(["git", "commit", "-m", "Initial broken commit"], cwd=project_dir, check=False, stdout=subprocess.DEVNULL)
    except Exception as e:
        print(f"Git init skipped: {e}")
        
    print("✓ Cursed project created!")
    print(f"To test: cd {project_dir} and run 'devready scan'")

if __name__ == "__main__":
    create_mock_project()
