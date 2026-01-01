import importlib
import sys


def run():
    import ui.cleaner_ui

    # Reload UI during development
    if "ui.cleaner_ui" in sys.modules:
        importlib.reload(ui.cleaner_ui)

    ui.cleaner_ui.show()
