import os
import sys
import json
import traceback
import pymxs

rt = pymxs.runtime


def _ensure_repo_on_path():
    # batch_runner.py is in <repo>/batch, so repo root is one level up
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    return repo_root


def run_on_file(max_path, out_dir, options):
    """
    Open a .max file, run clean steps, save, write report JSON.
    Returns dict summary.
    """
    result = {
        "file": max_path,
        "status": "ok",
        "errors": [],
        "actions": [],
    }

    try:
        # Load scene
        rt.loadMaxFile(max_path, useFileUnits=True, quiet=True)

        # Import tool logic
        from core.transform_fixes import clean_transforms
        from core.scene_cleanup import clean_scene

        actions = []
        actions += clean_transforms(options)
        actions += clean_scene(options)

        result["actions"] = actions

        # Save the file (overwrites!)
        rt.saveMaxFile(max_path, quiet=True)

    except Exception as e:
        result["status"] = "failed"
        result["errors"].append(str(e))
        result["errors"].append(traceback.format_exc())

    # Write per-file report
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(max_path))[0]
    report_path = os.path.join(out_dir, f"{base}_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    return result


def run_batch(input_dir, out_dir, options):
    summaries = []

    for root, _, files in os.walk(input_dir):
        for fn in files:
            if fn.lower().endswith(".max"):
                path = os.path.join(root, fn)
                print(f"[batch_runner] Processing: {path}")
                summaries.append(run_on_file(path, out_dir, options))

    os.makedirs(out_dir, exist_ok=True)
    summary_path = os.path.join(out_dir, "batch_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summaries, f, indent=2)

    print(f"[batch_runner] Done. Files: {len(summaries)}")
    print(f"[batch_runner] Summary: {summary_path}")


def main():
    _ensure_repo_on_path()

    # ? EDIT THESE TWO PATHS FOR YOUR MACHINE
    INPUT_DIR = r"C:\TEMP\max_in"
    OUT_DIR = r"C:\TEMP\max_reports"

    # Batch options (match your UI options)
    OPTIONS = {
        "reset_xform": True,
        "collapse_stack": True,
        "delete_hidden": False,
        "delete_frozen_helpers": False,
        "delete_empty_layers": True,
        "remove_unused_materials": False,  # Day 6+ (not in batch yet)
    }

    run_batch(INPUT_DIR, OUT_DIR, OPTIONS)


if __name__ == "__main__":
    main()
