import os
import pymxs
rt = pymxs.runtime


def relink_missing_textures(search_root):
    """
    Best-effort relink:
    - find missing BitmapTexture filenames
    - search for same basename under search_root
    - update bt.filename
    Returns actions list[dict]
    """
    actions = []

    if not search_root or not os.path.isdir(search_root):
        return [_warning("Relink", "Invalid search folder")]

    # Build index of files by basename (case-insensitive)
    file_map = {}
    for root, _, files in os.walk(search_root):
        for f in files:
            key = f.lower()
            if key not in file_map:
                file_map[key] = os.path.join(root, f)

    ms = r"""
    (
        local out = #()
        local bms = getClassInstances BitmapTexture
        for bt in bms do
        (
            if bt != undefined do
            (
                local p = bt.filename
                if p != undefined and p != "" do
                (
                    if (doesFileExist p) == false do append out bt
                )
            )
        )
        out
    )
    """

    missing_bts = []
    try:
        missing_bts = rt.execute(ms)
    except Exception:
        missing_bts = []

    if not missing_bts:
        return [_info("Relink", "No missing BitmapTexture nodes found.")]

    # One undo chunk in MAXScript for safety
    # We'll perform changes from Python but wrap with rt.undo label.
    def _do():
        for bt in list(missing_bts):
            try:
                old = str(bt.filename)
                base = os.path.basename(old).lower()
                if base in file_map:
                    new_path = file_map[base]
                    bt.filename = new_path
                    actions.append(_info(bt.name, f"Relinked to: {new_path}"))
                else:
                    actions.append(_warning(bt.name, f"Not found in folder: {base}"))
            except Exception:
                pass

    try:
        rt.undo("MaxSceneCleaner_RelinkTextures", _do)
    except Exception:
        # If undo wrapper is flaky, still do it
        _do()

    return actions


def _info(node, message):
    return {"level": "INFO", "node": node, "message": message}


def _warning(node, message):
    return {"level": "WARNING", "node": node, "message": message}
