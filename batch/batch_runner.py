import os
import sys
import json
import traceback
import pymxs

rt = pymxs.runtime


def ensure_repo_on_path():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    return repo_root


def run_on_file(src_max_path, dst_max_path, report_dir, options):
    """
    Open src .max, run cleaning, save to dst path, write report JSON.
    """
    result = {
        "src_file": src_max_path,
        "dst_file": dst_max_path,
        "status": "ok",
        "errors": [],
        "actions": [],
    }

    try:
        rt.loadMaxFile(src_max_path, useFileUnits=True, quiet=True)

        from core.transform_fixes import clean_transforms
        from core.scene_cleanup import clean_scene

        actions = []
        actions += clean_transforms(options)
        actions += clean_scene(options)
        result["actions"] = actions

        # ? Save as copy to output folder (safe)
        rt.saveMaxFile(dst_max_path, quiet=True)

    except Exception as e:
        result["status"] = "failed"
        result["errors"].append(str(e))
        result["errors"].append(traceback.format_exc())

    os.makedirs(report_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(src_max_path))[0]
    report_path = os.path.join(report_dir, f"{base}_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    return result


def collect_max_files(input_dir):
    max_files = []
    for root, _, files in os.walk(input_dir):
        for fn in files:
            if fn.lower().endswith(".max"):
                max_files.append(os.path.join(root, fn))
    return max_files


def run_batch(input_dir, output_dir, options):
    """
    Runs batch in the current Max session (open -> clean -> save copy).
    Writes reports to <output_dir>/reports.
    """
    ensure_repo_on_path()

    input_dir = os.path.abspath(input_dir)
    output_dir = os.path.abspath(output_dir)
    report_dir = os.path.join(output_dir, "reports")
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(report_dir, exist_ok=True)

    files = collect_max_files(input_dir)

    summaries = []
    for src in files:
        rel = os.path.relpath(src, input_dir)
        dst = os.path.join(output_dir, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)

        print(f"[batch_runner] Processing: {src}")
        summaries.append(run_on_file(src, dst, report_dir, options))

    summary_path = os.path.join(report_dir, "batch_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summaries, f, indent=2)

    print(f"[batch_runner] Done. Files: {len(summaries)}")
    print(f"[batch_runner] Summary: {summary_path}")

    return summary_path
