import importlib
import sys

__version__ = "1.0.0"

def run():
    import ui.cleaner_ui

    # Reload UI during development
    if "ui.cleaner_ui" in sys.modules:
        importlib.reload(ui.cleaner_ui)

    ui.cleaner_ui.show()
