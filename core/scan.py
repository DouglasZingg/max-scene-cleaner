import pymxs
rt = pymxs.runtime


def scan_scene(options):
    """
    Day 2: stub scan.
    Returns a few representative issues based on scene content.
    """
    results = []

    objs = list(rt.objects)
    if not objs:
        return results

    # Example stub issues:
    # - warn if more than N objects
    if len(objs) > 200:
        results.append(_warning("Scene", f"High object count: {len(objs)}"))

    # - warn if any selected object exists (so user can test quickly)
    sel = list(rt.selection)
    if sel:
        results.append(_info(sel[0].name, "Selected object detected (stub check)"))

    # - show chosen options (helps confirm UI wiring)
    enabled = [k for k, v in options.items() if v]
    results.append(_info("Options", f"Enabled: {', '.join(enabled)}"))

    return results


def _warning(node, message):
    return {"level": "WARNING", "node": node, "message": message}


def _info(node, message):
    return {"level": "INFO", "node": node, "message": message}
