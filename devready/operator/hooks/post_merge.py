import sys
import logging

logger = logging.getLogger(__name__)

def main():
    import subprocess
    print("DevReady: Running scan after merge...")
    try:
        result = subprocess.run(
            ["devready", "scan", "--scope", "full"],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            print("DevReady: Drift detected after merge. Run 'devready status' for details.")
        else:
            print("DevReady: Environment looks good after merge.")
    except Exception as e:
        logger.debug("DevReady post-merge scan skipped: %s", e)
    sys.exit(0)

if __name__ == "__main__":
    main()
