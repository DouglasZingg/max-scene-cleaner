import pymxs
rt = pymxs.runtime


def clean_transforms(options):
    """
    Transform cleanup with ONE reliable undo step by executing a MAXScript undo block.

    options:
      - reset_xform (bool)
      - collapse_stack (bool)

    Returns:
      actions: list[dict]
    """
    actions = []

    do_reset = bool(options.get("reset_xform", True))
    do_collapse = bool(options.get("collapse_stack", True))

    targets = _get_geometry_nodes()
    if not targets:
        return actions

    # Build handle list (stable identifiers for MAXScript)
    handles = []
    for n in targets:
        try:
            handles.append(int(rt.getHandleByAnim(n)))
        except Exception:
            pass

    if not handles:
        return actions

    # Create MAXScript array: #(123,456,789)
    handles_ms = "#(" + ",".join(str(h) for h in handles) + ")"

    # Build one undo block in MAXScript (most reliable for Ctrl+Z)
    # Reset XForm adds an XForm modifier; collapse bakes it; convertToPoly ensures clean base object.
    ms = f"""
    undo "MaxSceneCleaner_TransformFixes" on
    (
        local hs = {handles_ms}
        for h in hs do
        (
            local n = getNodeByHandle h
            if n != undefined do
            (
                if {str(do_reset).lower()} do
                (
                    resetXForm n
                )

                if {str(do_collapse).lower()} do
                (
                    collapseStack n
                    try(convertToPoly n)catch()
                )
            )
        )
    )
    """

    try:
        rt.execute(ms)
        actions.append(_info("Scene", f"Transform cleanup applied to {len(handles)} geometry objects"))
    except Exception:
        actions.append(_warning("Scene", "Transform cleanup failed (MAXScript execution error)"))

    # Force UI update (Modify panel often needs this)
    try:
        rt.redrawViews()
        rt.completeRedraw()
    except Exception:
        pass

    return actions


# ---------------------------
# Helpers
# ---------------------------
def _get_geometry_nodes():
    out = []
    for o in rt.objects:
        try:
            sc = rt.superClassOf(o)
            if str(sc) == "geometryClass":
                out.append(o)
        except Exception:
            pass
    return out


def _info(node, message):
    return {"level": "INFO", "node": node, "message": message}


def _warning(node, message):
    return {"level": "WARNING", "node": node, "message": message}
