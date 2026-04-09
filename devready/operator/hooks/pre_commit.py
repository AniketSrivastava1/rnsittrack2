import sys
import logging

logger = logging.getLogger(__name__)

def main():
    import subprocess
    print("DevReady: Validating environment before commit...")
    try:
        result = subprocess.run(
            ["devready", "scan", "--scope", "system"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            print("DevReady: Environment issues detected. Run 'devready status' for details.")
            # Non-blocking — don't fail the commit, just warn
        else:
            print("DevReady: Environment OK.")
    except Exception as e:
        logger.debug("DevReady pre-commit check skipped: %s", e)
    sys.exit(0)

if __name__ == "__main__":
    main()
