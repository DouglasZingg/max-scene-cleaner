import os
import sys
import importlib
import traceback


def run():
    try:
        repo_root = os.path.dirname(os.path.abspath(__file__))
        if repo_root not in sys.path:
            sys.path.insert(0, repo_root)

        # ? clear project modules so edits always apply
        for m in list(sys.modules.keys()):
            if m == "main" or m.startswith("ui.") or m.startswith("core.") or m.startswith("batch."):
                del sys.modules[m]

        import main
        importlib.reload(main)
        main.run()

        print("[max_launcher] Launched Max Scene Cleaner.")
    except Exception:
        print("[max_launcher] Failed to launch:")
        traceback.print_exc()
