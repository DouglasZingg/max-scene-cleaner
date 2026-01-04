import pymxs
rt = pymxs.runtime


def clean_scene(options):
    """
    Day 5: Cleanup actions (delete hidden, delete frozen helpers, delete empty layers)
    Runs as a single MAXScript undo block (reliable Ctrl+Z once).

    Max 2026 notes (based on your runtime behavior):
      - LayerProperties.nodes(...) wants 1 argument; nodes() with 0 args fails
      - LayerManager.deleteLayer does NOT exist
      - LayerManager.deleteLayerByName DOES exist
    """

    do_hidden = bool(options.get("delete_hidden", False))
    do_frozen_helpers = bool(options.get("delete_frozen_helpers", False))
    do_empty_layers = bool(options.get("delete_empty_layers", False))

    before = {
        "hidden": _count_hidden_objects() if do_hidden else 0,
        "frozen_helpers": _count_frozen_helpers() if do_frozen_helpers else 0,
        "empty_layers": _count_empty_layers_by_object_scan() if do_empty_layers else 0,
    }

    ms_hidden = "true" if do_hidden else "false"
    ms_frozen = "true" if do_frozen_helpers else "false"
    ms_layers = "true" if do_empty_layers else "false"

    # Robust empty-layer detection: scan all objects and check node.layer == lyr
    # Robust deletion: use LayerManager.deleteLayerByName (available in your build), fallback lyr.delete()
    ms = f"""
    undo "MaxSceneCleaner_SceneCleanup" on
    (
        local deletedHidden = 0
        local deletedFrozenHelpers = 0
        local deletedEmptyLayers = 0

        -- Delete hidden objects
        if {ms_hidden} do
        (
            for n in objects do
            (
                if isValidNode n and n.isHidden do
                (
                    try(delete n)catch()
                    deletedHidden += 1
                )
            )
        )

        -- Delete frozen helpers
        if {ms_frozen} do
        (
            for n in helpers do
            (
                if isValidNode n and n.isFrozen do
                (
                    try(delete n)catch()
                    deletedFrozenHelpers += 1
                )
            )
        )

        -- Delete empty layers (Max 2026 safe)
        if {ms_layers} do
        (
            local lm = LayerManager

            -- ensure we're not on a deletable layer
            try(lm.setCurrent (lm.getLayer 0))catch()

            for i = (lm.count-1) to 0 by -1 do
            (
                local lyr = lm.getLayer i
                if lyr != undefined do
                (
                    local lname = toLower lyr.name
                    if lname != "0" do
                    (
                        -- Count nodes by scanning scene objects (avoids lyr.nodes API differences)
                        local ct = 0
                        for n in objects do
                        (
                            if isValidNode n and n.layer == lyr do ct += 1
                        )

                        if ct == 0 do
                        (
                            -- If somehow current, switch away
                            try(if lyr == lm.getCurrent() do lm.setCurrent (lm.getLayer 0))catch()

                            local nm = lyr.name
                            local deletedOK = false

                            -- Preferred in your build
                            try
                            (
                                lm.deleteLayerByName nm
                                deletedOK = true
                            )
                            catch()

                            -- Fallback (some builds support this)
                            if not deletedOK do
                            (
                                try(lyr.delete(); deletedOK = true)catch()
                            )

                            if deletedOK do deletedEmptyLayers += 1
                        )
                    )
                )
            )
        )

        format "MaxSceneCleaner cleanup: hidden=% frozenHelpers=% emptyLayers=%\\n" deletedHidden deletedFrozenHelpers deletedEmptyLayers
    )
    """

    actions = []
    try:
        rt.execute(ms)
        actions.append(_info("Scene", "Cleanup complete (hidden/frozen/layers)"))
    except Exception as e:
        actions.append(_warning("Scene", f"Cleanup failed: {e}"))
        return actions

    # Force UI refresh
    try:
        rt.redrawViews()
        rt.completeRedraw()
    except Exception:
        pass

    after = {
        "hidden": _count_hidden_objects() if do_hidden else 0,
        "frozen_helpers": _count_frozen_helpers() if do_frozen_helpers else 0,
        "empty_layers": _count_empty_layers_by_object_scan() if do_empty_layers else 0,
    }

    # UI-friendly summary
    if do_hidden:
        actions.append(_info("Scene", f"Hidden objects: {before['hidden']} -> {after['hidden']}"))
    if do_frozen_helpers:
        actions.append(_info("Scene", f"Frozen helpers: {before['frozen_helpers']} -> {after['frozen_helpers']}"))
    if do_empty_layers:
        actions.append(_info("Scene", f"Empty layers: {before['empty_layers']} -> {after['empty_layers']}"))

    return actions


# ---------------------------
# Counting helpers (Python-side)
# ---------------------------
def _count_hidden_objects():
    try:
        return sum(1 for n in rt.objects if rt.isValidNode(n) and n.isHidden)
    except Exception:
        return 0


def _count_frozen_helpers():
    try:
        return sum(1 for n in rt.helpers if rt.isValidNode(n) and n.isFrozen)
    except Exception:
        return 0


def _count_empty_layers_by_object_scan():
    """
    Robust across Max versions:
    - iterate layers
    - count nodes by scanning objects where obj.layer == layer
    """
    total = 0
    try:
        lm = rt.LayerManager
        for i in range(lm.count):
            lyr = lm.getLayer(i)
            if not lyr:
                continue
            try:
                if str(lyr.name).lower() == "0":
                    continue
            except Exception:
                continue

            ct = 0
            try:
                for n in rt.objects:
                    try:
                        if rt.isValidNode(n) and n.layer == lyr:
                            ct += 1
                    except Exception:
                        pass
            except Exception:
                pass

            if ct == 0:
                total += 1
    except Exception:
        pass

    return total


# ---------------------------
# Result helpers
# ---------------------------
def _info(node, message):
    return {"level": "INFO", "node": node, "message": message}


def _warning(node, message):
    return {"level": "WARNING", "node": node, "message": message}
