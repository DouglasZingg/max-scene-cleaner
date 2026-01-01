import os
import sys
import importlib
import traceback


def run():
    try:
        repo_root = os.path.dirname(os.path.abspath(__file__))
        if repo_root not in sys.path:
            sys.path.insert(0, repo_root)

        import main
        importlib.reload(main)
        main.run()

        print("[max_launcher] Launched Max Scene Cleaner.")
    except Exception:
        print("[max_launcher] Failed to launch:")
        traceback.print_exc()
