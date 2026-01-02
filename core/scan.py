import pymxs
rt = pymxs.runtime


def scan_scene(options):
    """
    Day 3: real scene scanning (read-only).

    options keys:
      - reset_xform (not applied today, but influences severity messaging)
      - collapse_stack (not applied today)
      - delete_hidden (flag hidden objects)
      - delete_frozen_helpers (flag frozen helpers)
      - delete_empty_layers (flag empty layers)
      - remove_unused_materials (best-effort warning today)
    """
    results = []

    objs = list(rt.objects)
    if not objs:
        return results

    # 1) Transform issues (pos/rot/scale)
    results.extend(_scan_transforms(objs))

    # 2) Hidden objects (only if option enabled)
    if options.get("delete_hidden", False):
        results.extend(_scan_hidden(objs))

    # 3) Frozen helpers (only if option enabled)
    if options.get("delete_frozen_helpers", False):
        results.extend(_scan_frozen_helpers(objs))

    # 4) Empty layers (only if option enabled)
    if options.get("delete_empty_layers", False):
        results.extend(_scan_empty_layers())

    # 5) Materials (best-effort today)
    if options.get("remove_unused_materials", False):
        results.extend(_scan_materials_best_effort())

    # 6) Light naming checks (always on, small signal)
    results.extend(_scan_naming(objs))

    return results


# ---------------------------
# Scans
# ---------------------------
def _scan_transforms(objs):
    out = []
    for o in objs:
        # Skip cameras/lights if you want a cleaner signal (optional)
        cls = rt.classOf(o)
        if str(cls) in ("Targetobject",):
            continue

        # Position
        try:
            p = o.position
            if _abs(p.x) > 0.001 or _abs(p.y) > 0.001 or _abs(p.z) > 0.001:
                out.append(_warning(o.name, f"Position not reset: ({p.x:.3f}, {p.y:.3f}, {p.z:.3f})"))
        except Exception:
            pass

        # Rotation (Euler)
        try:
            r = o.rotation
            # rotation can be a quat; convert to euler angles
            e = rt.eulerAngles(r)
            if _abs(e.x) > 0.01 or _abs(e.y) > 0.01 or _abs(e.z) > 0.01:
                out.append(_warning(o.name, f"Rotation not reset: ({e.x:.2f}, {e.y:.2f}, {e.z:.2f})"))
        except Exception:
            pass

        # Scale
        try:
            s = o.scale
            # scale can be Point3
            if _abs(s.x - 1.0) > 0.001 or _abs(s.y - 1.0) > 0.001 or _abs(s.z - 1.0) > 0.001:
                out.append(_warning(o.name, f"Scale not 1: ({s.x:.3f}, {s.y:.3f}, {s.z:.3f})"))
        except Exception:
            pass

        # Modifier stack count (useful early signal)
        try:
            mod_count = o.modifiers.count
            if mod_count > 8:
                out.append(_info(o.name, f"High modifier stack count: {mod_count} (consider collapsing)"))
        except Exception:
            pass

    return out


def _scan_hidden(objs):
    out = []
    for o in objs:
        try:
            if o.isHidden:
                out.append(_info(o.name, "Object is hidden (cleanup option enabled)"))
        except Exception:
            pass
    return out


def _scan_frozen_helpers(objs):
    out = []
    for o in objs:
        try:
            if o.isFrozen:
                # Helpers include Point, Dummy, etc. Class check is a bit fuzzy, so use superclass
                sc = rt.superClassOf(o)
                if str(sc) == "helper":
                    out.append(_info(o.name, "Frozen helper detected (cleanup option enabled)"))
                else:
                    out.append(_info(o.name, "Frozen object detected (cleanup option enabled)"))
        except Exception:
            pass
    return out


def _scan_empty_layers():
    out = []
    try:
        lm = rt.LayerManager
        layer_count = lm.count

        for i in range(layer_count):
            layer = lm.getLayer(i)
            if layer is None:
                continue

            # Skip default layer
            try:
                lname = (layer.name or "").lower()
                if lname in ("0", "default", "default layer"):
                    continue
            except Exception:
                lname = "unknown"

            # Robust "is empty?" checks across versions
            node_count = None

            # 1) Preferred: layer.nodes collection (most reliable)
            try:
                nodes = layer.nodes
                # nodes.count usually works
                node_count = nodes.count
            except Exception:
                pass

            # 2) Fallback: try layer.getNumNodes() (exists in some builds)
            if node_count is None:
                try:
                    node_count = layer.getNumNodes()
                except Exception:
                    pass

            # 3) Last resort: try layer.count (may not be node count)
            if node_count is None:
                try:
                    node_count = layer.count
                except Exception:
                    node_count = 0  # fail-safe

            if int(node_count) == 0:
                out.append(_info(f"Layer:{layer.name}", "Empty layer"))

    except Exception:
        pass

    return out

def _scan_materials_best_effort():
    out = []
    try:
        # Scene material library (not perfect for unused detection)
        scene_mats = rt.sceneMaterials
        count = scene_mats.count
        if count > 50:
            out.append(_warning("Scene", f"High material count: {count} (unused cleanup recommended)"))
        elif count > 0:
            out.append(_info("Scene", f"Scene materials detected: {count} (unused cleanup later)"))
    except Exception:
        pass
    return out


def _scan_naming(objs):
    out = []
    for o in objs:
        try:
            name = o.name
            if " " in name:
                out.append(_warning(name, "Name contains spaces"))
            if any(c.isupper() for c in name):
                out.append(_info(name, "Name contains uppercase (studio pipelines often prefer lowercase)"))
        except Exception:
            pass
    return out


# ---------------------------
# Helpers
# ---------------------------
def _abs(v):
    try:
        return abs(float(v))
    except Exception:
        return 0.0


def _warning(node, message):
    return {"level": "WARNING", "node": node, "message": message}


def _info(node, message):
    return {"level": "INFO", "node": node, "message": message}
