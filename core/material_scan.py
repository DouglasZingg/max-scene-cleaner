import pymxs
rt = pymxs.runtime


def scan_materials_and_textures(options=None):
    """
    Day 6: read-only material/texture scan.
    Returns list[dict]: {"level","node","message"}

    We detect:
      - missing bitmap files
      - high scene material count (best-effort)
    """
    results = []

    # 1) High material count (best-effort)
    try:
        sm = rt.sceneMaterials
        mat_count = int(sm.count)
        if mat_count > 50:
            results.append(_warning("Scene", f"High scene material count: {mat_count}"))
        elif mat_count > 0:
            results.append(_info("Scene", f"Scene materials: {mat_count}"))
    except Exception:
        pass

    # 2) Missing textures (robust via MAXScript bitmap collection)
    ms = r"""
    (
        local out = #()  -- array of strings "owner|path"
        local bms = getClassInstances BitmapTexture

        for bt in bms do
        (
            if bt != undefined do
            (
                local p = bt.filename
                if p != undefined and p != "" do
                (
                    if (doesFileExist p) == false do
                    (
                        local owner = ""
                        try(owner = bt.name)catch(owner = "BitmapTexture")
                        append out (owner + "|" + p)
                    )
                )
            )
        )

        out
    )
    """

    missing = []
    try:
        missing = rt.execute(ms)  # returns MAXScript array
    except Exception:
        missing = []

    try:
        # Convert MAXScript array-ish to python iterable
        for s in list(missing):
            try:
                parts = str(s).split("|", 1)
                owner = parts[0] if len(parts) > 0 else "Bitmap"
                path = parts[1] if len(parts) > 1 else str(s)
                results.append(_warning(owner, f"Missing texture: {path}"))
            except Exception:
                pass
    except Exception:
        pass

    if not missing:
        results.append(_info("Textures", "No missing bitmap textures detected (BitmapTexture)."))

    return results


def _info(node, message):
    return {"level": "INFO", "node": node, "message": message}


def _warning(node, message):
    return {"level": "WARNING", "node": node, "message": message}
