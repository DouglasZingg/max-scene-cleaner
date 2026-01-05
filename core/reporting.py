import os
import json
import datetime


TOOL_NAME = "Max Scene Cleaner"
TOOL_VERSION = "1.0"


def now_iso():
    return datetime.datetime.now().isoformat(timespec="seconds")


def build_report(options, scan_results, action_results):
    return {
        "tool": {"name": TOOL_NAME, "version": TOOL_VERSION},
        "timestamp": now_iso(),
        "options": options,
        "scan_results": scan_results,
        "actions": action_results,
        "summary": {
            "scan_warning_count": sum(1 for r in scan_results if r.get("level") == "WARNING"),
            "scan_info_count": sum(1 for r in scan_results if r.get("level") == "INFO"),
            "action_warning_count": sum(1 for r in action_results if r.get("level") == "WARNING"),
            "action_info_count": sum(1 for r in action_results if r.get("level") == "INFO"),
        },
    }


def save_json(report, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    return path


def save_html(report, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    def esc(s):
        return (
            str(s)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )

    scan_rows = "\n".join(
        "<tr><td>{}</td><td>{}</td><td>{}</td></tr>".format(
            esc(r.get("level")), esc(r.get("node")), esc(r.get("message"))
        )
        for r in report.get("scan_results", [])
    )

    act_rows = "\n".join(
        "<tr><td>{}</td><td>{}</td><td>{}</td></tr>".format(
            esc(r.get("level")), esc(r.get("node")), esc(r.get("message"))
        )
        for r in report.get("actions", [])
    )

    html = """<!doctype html>
<html>
<head>
<meta charset="utf-8"/>
<title>{title} Report</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 24px; }}
h1 {{ margin-bottom: 4px; }}
.small {{ color: #666; margin-top: 0; }}
table {{ border-collapse: collapse; width: 100%; margin: 12px 0 28px; }}
th, td {{ border: 1px solid #ddd; padding: 8px; font-size: 13px; }}
th {{ background: #f5f5f5; text-align: left; }}
.level-WARNING {{ color: #b45309; font-weight: bold; }}
.level-INFO {{ color: #1f2937; }}
code {{ background: #f7f7f7; padding: 2px 6px; border-radius: 4px; }}
</style>
</head>
<body>

<h1>{title}</h1>
<p class="small">Version <code>{version}</code> - {timestamp}</p>

<h2>Summary</h2>
<ul>
  <li>Scan warnings: <b>{sw}</b></li>
  <li>Scan info: <b>{si}</b></li>
  <li>Action warnings: <b>{aw}</b></li>
  <li>Action info: <b>{ai}</b></li>
</ul>

<h2>Options</h2>
<pre>{options}</pre>

<h2>Scan Results</h2>
<table>
<thead><tr><th>Level</th><th>Node</th><th>Message</th></tr></thead>
<tbody>
{scan_rows}
</tbody>
</table>

<h2>Cleanup Actions</h2>
<table>
<thead><tr><th>Level</th><th>Node</th><th>Message</th></tr></thead>
<tbody>
{act_rows}
</tbody>
</table>

</body>
</html>
""".format(
        title=esc(report["tool"]["name"]),
        version=esc(report["tool"]["version"]),
        timestamp=esc(report["timestamp"]),
        sw=report["summary"]["scan_warning_count"],
        si=report["summary"]["scan_info_count"],
        aw=report["summary"]["action_warning_count"],
        ai=report["summary"]["action_info_count"],
        options=esc(json.dumps(report.get("options", {}), indent=2)),
        scan_rows=scan_rows,
        act_rows=act_rows,
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)

    return path
