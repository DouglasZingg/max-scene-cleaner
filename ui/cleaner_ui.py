# Qt compatibility across Max versions
try:
    from PySide6 import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui

import pymxs
rt = pymxs.runtime


def get_max_main_window():
    """
    Max 2026-safe: find the main window from Qt top-level widgets.
    """
    app = QtWidgets.QApplication.instance()
    if not app:
        return None

    candidates = []
    for w in QtWidgets.QApplication.topLevelWidgets():
        title = (w.windowTitle() or "").lower()
        name = (w.objectName() or "").lower()
        if "3ds" in title or "3ds" in name or "autodesk" in title:
            candidates.append(w)

    # Best guess: the largest visible candidate
    if candidates:
        candidates.sort(key=lambda x: x.width() * x.height(), reverse=True)
        return candidates[0]

    return None


class MaxSceneCleanerUI(QtWidgets.QDialog):
    def __init__(self, parent=get_max_main_window()):
        super().__init__(parent)

        self.setWindowTitle("3ds Max Scene Cleaner")
        self.setMinimumSize(640, 420)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)

        self.last_results = []

        self.build_ui()
        self.connect_signals()

    # ---------------------------
    # UI
    # ---------------------------
    def build_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)

        # Header
        header = QtWidgets.QLabel("Scene Cleaner / Batch Prep Tool")
        header.setStyleSheet("font-size: 16px; font-weight: bold;")
        main_layout.addWidget(header)

        sub = QtWidgets.QLabel("Day 2: UI Skeleton (Scan + Clean stubs)")
        sub.setStyleSheet("color: gray;")
        main_layout.addWidget(sub)

        # Options group
        opts = QtWidgets.QGroupBox("Cleanup Options")
        opts_layout = QtWidgets.QGridLayout(opts)

        self.chk_reset_xform = QtWidgets.QCheckBox("Reset XForm")
        self.chk_collapse_stack = QtWidgets.QCheckBox("Collapse Stack")
        self.chk_delete_hidden = QtWidgets.QCheckBox("Delete Hidden Objects")
        self.chk_delete_frozen = QtWidgets.QCheckBox("Delete Frozen Helpers")
        self.chk_delete_empty_layers = QtWidgets.QCheckBox("Delete Empty Layers")
        self.chk_remove_unused_mats = QtWidgets.QCheckBox("Remove Unused Materials")

        # Good defaults for a cleaner tool
        self.chk_reset_xform.setChecked(True)
        self.chk_collapse_stack.setChecked(True)
        self.chk_delete_hidden.setChecked(False)
        self.chk_delete_frozen.setChecked(False)
        self.chk_delete_empty_layers.setChecked(True)
        self.chk_remove_unused_mats.setChecked(True)

        opts_layout.addWidget(self.chk_reset_xform, 0, 0)
        opts_layout.addWidget(self.chk_collapse_stack, 0, 1)
        opts_layout.addWidget(self.chk_delete_hidden, 1, 0)
        opts_layout.addWidget(self.chk_delete_frozen, 1, 1)
        opts_layout.addWidget(self.chk_delete_empty_layers, 2, 0)
        opts_layout.addWidget(self.chk_remove_unused_mats, 2, 1)

        main_layout.addWidget(opts)

        # Buttons row
        btn_layout = QtWidgets.QHBoxLayout()

        self.btn_scan = QtWidgets.QPushButton("Scan Scene")
        self.btn_clean = QtWidgets.QPushButton("Clean Scene")
        self.btn_export = QtWidgets.QPushButton("Export Report")
        self.btn_clear = QtWidgets.QPushButton("Clear Results")

        self.btn_export.setEnabled(False)  # enable on Day 8 equivalent

        btn_layout.addWidget(self.btn_scan)
        btn_layout.addWidget(self.btn_clean)
        btn_layout.addWidget(self.btn_export)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_clear)

        main_layout.addLayout(btn_layout)

        # Results list
        self.results_list = QtWidgets.QListWidget()
        self.results_list.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        main_layout.addWidget(self.results_list)

        # Status bar
        self.status_label = QtWidgets.QLabel("Ready")
        self.status_label.setStyleSheet("color: gray;")
        main_layout.addWidget(self.status_label)

    def connect_signals(self):
        self.btn_scan.clicked.connect(self.on_scan)
        self.btn_clean.clicked.connect(self.on_clean)
        self.btn_clear.clicked.connect(self.on_clear)

    # ---------------------------
    # Actions (stubs for Day 2)
    # ---------------------------
    def on_scan(self):
        from core.scan import scan_scene

        self.status_label.setText("Scanning scene...")
        self.results_list.clear()

        options = self.get_options()
        results = scan_scene(options)

        self.last_results = results

        if not results:
            self.add_result("INFO", "No issues found (stub scan).")
        else:
            for r in results:
                self.add_result(r["level"], f"{r['node']} - {r['message']}")

        self.status_label.setText(f"Scan complete. Issues: {len(results)}")

    def on_clean(self):
        from core.transform_fixes import clean_transforms

        self.status_label.setText("Cleaning scene (transforms)...")
        self.add_result("INFO", "Starting transform cleanup...")

        options = self.get_options()
        actions = clean_transforms(options)

        if not actions:
            self.add_result("INFO", "No geometry objects found to clean.")
            self.status_label.setText("Clean complete (nothing to do)")
            return

        for a in actions:
            self.add_result(a["level"], f"{a['node']} - {a['message']}")

        self.status_label.setText(f"Clean complete. Actions: {len(actions)}")


    def on_clear(self):
        self.results_list.clear()
        self.last_results = []
        self.status_label.setText("Results cleared")

    # ---------------------------
    # Helpers
    # ---------------------------
    def get_options(self):
        return {
            "reset_xform": self.chk_reset_xform.isChecked(),
            "collapse_stack": self.chk_collapse_stack.isChecked(),
            "delete_hidden": self.chk_delete_hidden.isChecked(),
            "delete_frozen_helpers": self.chk_delete_frozen.isChecked(),
            "delete_empty_layers": self.chk_delete_empty_layers.isChecked(),
            "remove_unused_materials": self.chk_remove_unused_mats.isChecked(),
        }

    def add_result(self, level, message):
        item = QtWidgets.QListWidgetItem(f"[{level}] {message}")

        if level == "ERROR":
            item.setForeground(QtGui.QColor("red"))
        elif level == "WARNING":
            item.setForeground(QtGui.QColor("orange"))
        else:
            item.setForeground(QtGui.QColor("white"))

        self.results_list.addItem(item)


# ---------------------------
# Window launcher (single instance)
# ---------------------------
_window = None


def show():
    global _window
    try:
        if _window is not None:
            _window.close()
            _window.deleteLater()
    except Exception:
        pass

    _window = MaxSceneCleanerUI()
    _window.show()
