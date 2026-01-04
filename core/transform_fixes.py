import pymxs
rt = pymxs.runtime


def clean_transforms(options):
    """
    Day 4: Reliable transform cleanup (Max 2026)
    - Uses a single MAXScript undo block
    - Iterates over built-in 'geometry' set (no handles)
    - Applies resetXForm + collapseStack + convertToPoly
    """
    do_reset = bool(options.get("reset_xform", True))
    do_collapse = bool(options.get("collapse_stack", True))

    # MAXScript uses 'true/false'
    ms_do_reset = "true" if do_reset else "false"
    ms_do_collapse = "true" if do_collapse else "false"

    ms = f"""
    undo "MaxSceneCleaner_TransformFixes" on
    (
        local changed = 0

        for n in geometry do
        (
            if isValidNode n do
            (
                -- Optional: Reset XForm
                if {ms_do_reset} do
                (
                    try(resetXForm n)catch()
                )

                -- Optional: Collapse Stack (bakes modifiers like Bend)
                if {ms_do_collapse} do
                (
                    try(collapseStack n)catch()
                )

                -- Ensure clean base object
                try(convertToPoly n)catch()

                changed += 1
            )
        )

        format "MaxSceneCleaner: cleaned % nodes\\n" changed
    )
    """

    actions = []
    try:
        before = _count_modifiers_on_geometry()
        rt.execute(ms)
        actions.append(_info("Scene", "Transform cleanup completed (geometry set)"))
    except Exception as e:
        actions.append(_warning("Scene", f"Transform cleanup failed: {e}"))
        return actions

    # Force UI refresh
    try:
        rt.redrawViews()
        rt.completeRedraw()
        after = _count_modifiers_on_geometry()
        actions.append(_info("Scene", f"Modifiers on geometry (before -> after): {before} -> {after}"))
    except Exception:
        pass

    return actions


def _info(node, message):
    return {"level": "INFO", "node": node, "message": message}


def _warning(node, message):
    return {"level": "WARNING", "node": node, "message": message}

def _count_modifiers_on_geometry():
    total = 0
    try:
        for n in rt.geometry:
            if rt.isValidNode(n):
                total += int(n.modifiers.count)
    except Exception:
        pass
    return total
