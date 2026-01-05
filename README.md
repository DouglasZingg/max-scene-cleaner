# Max Scene Cleaner (3ds Max 2026) — v1.0.0

Production-style pipeline utility for cleaning and validating 3ds Max scenes before export/hand-off.

## Features
### Scan
- Naming and transform warnings (pipeline-friendly checks)
- Empty layer detection (Max 2026 safe)

### Clean (single undo)
- Reset XForm + Collapse Stack (reliable in Max 2026)
- Delete hidden objects (optional)
- Delete frozen helpers (optional)
- Delete empty layers (robust across layer API differences)

### Materials / Textures
- Detect missing BitmapTexture files
- Relink missing textures by searching a folder

### Batch
- Batch process folders of `.max` files inside Max
- Save cleaned copies to an output folder
- JSON reports per file + batch summary

### Reporting
- Export scene report as JSON + HTML from the UI

## Tech
- Python (pymxs runtime)
- Qt (PySide in 3ds Max 2026)
- MAXScript execution for version-stable operations (undo chunks + layer ops)

## Install / Run
1) Clone repo
2) In 3ds Max: **Scripting > New Script** (Python tab)
3) Run:

```python
import sys
sys.path.insert(0, r"C:\path\to\max-scene-cleaner")
import max_launcher
max_launcher.run()

***TESTING
# Testing Checklist

## Scene Prep
- Create a box, add Bend modifier
- Create empty layers Layer001/Layer002 (no selection)
- Create a hidden object
- Create a frozen dummy helper
- Create a BitmapTexture with a missing file path

## Validate
- Scan Scene shows warnings
- Scan Materials shows missing texture

## Clean
- Clean removes Bend via collapse
- Clean removes empty layers
- Clean removes hidden/frozen if enabled
- Ctrl+Z once restores everything

## Export
- Export JSON + HTML
- HTML tables display results
