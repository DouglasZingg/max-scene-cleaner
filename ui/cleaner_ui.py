# Qt compatibility across Max versions
try:
    from PySide6 import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui

import pymxs
import os
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
        self.btn_scan_mats = QtWidgets.QPushButton("Scan Materials")
        self.btn_clean = QtWidgets.QPushButton("Clean Scene")
        self.btn_relink = QtWidgets.QPushButton("Relink Textures...")
        self.btn_export = QtWidgets.QPushButton("Export Report")
        self.btn_clear = QtWidgets.QPushButton("Clear Results")
        self.btn_batch = QtWidgets.QPushButton("Batch Clean Folder...")
        self.btn_open_reports = QtWidgets.QPushButton("Open Reports Folder")

        self.btn_export.setEnabled(False)

        btn_layout.addWidget(self.btn_scan)
        btn_layout.addWidget(self.btn_scan_mats)
        btn_layout.addWidget(self.btn_clean)
        btn_layout.addWidget(self.btn_relink)
        btn_layout.addWidget(self.btn_export)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_clear)
        btn_layout.addWidget(self.btn_batch)
        btn_layout.addWidget(self.btn_open_reports)

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
        self.btn_scan_mats.clicked.connect(self.on_scan_materials)
        self.btn_relink.clicked.connect(self.on_relink_textures)
        self.btn_batch.clicked.connect(self.on_batch_clean)
        self.btn_batch.clicked.connect(self.on_batch_clean)
        self.btn_open_reports.clicked.connect(self.on_open_reports)


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
        
        warns = sum(1 for r in results if r.get("level") == "WARNING")
        infos = sum(1 for r in results if r.get("level") == "INFO")
        self.add_result("INFO", f"Summary: {warns} warnings, {infos} info")

    def on_clean(self):
        from core.transform_fixes import clean_transforms
        from core.scene_cleanup import clean_scene

        self.status_label.setText("Cleaning scene...")
        self.add_result("INFO", "Starting cleanup...")

        options = self.get_options()

        actions = []

        # Day 4: transforms (Reset XForm + Collapse Stack)
        actions += clean_transforms(options)

        # Day 5: hidden / frozen helpers / empty layers
        actions += clean_scene(options)

        if not actions:
            self.add_result("INFO", "Nothing changed. (No targets found or options disabled.)")
            self.status_label.setText("Clean complete (no changes)")
            return

        # Display results
        for a in actions:
            self.add_result(a["level"], f"{a['node']} - {a['message']}")

        # Optional: rerun scan after cleaning (nice UX)
        try:
            from core.scan import scan_scene
            scan_results = scan_scene(options)
            self.add_result("INFO", f"Post-clean scan issues: {len(scan_results)}")
        except Exception:
            pass

        self.status_label.setText("Clean complete")

    def on_clear(self):
        self.results_list.clear()
        self.last_results = []
        self.status_label.setText("Results cleared")
        
    def on_scan_materials(self):
        from core.material_scan import scan_materials_and_textures

        self.status_label.setText("Scanning materials/textures...")
        self.add_result("INFO", "Material/texture scan started...")

        results = scan_materials_and_textures(self.get_options())
        for r in results:
            self.add_result(r["level"], f"{r['node']} - {r['message']}")

        warns = sum(1 for r in results if r.get("level") == "WARNING")
        self.status_label.setText(f"Material scan complete. Warnings: {warns}")


    def on_relink_textures(self):
        from core.texture_relink import relink_missing_textures

        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Texture Search Folder")
        if not folder:
            self.add_result("INFO", "Relink canceled.")
            return

        self.status_label.setText("Relinking textures...")
        actions = relink_missing_textures(folder)

        for a in actions:
            self.add_result(a["level"], f"{a['node']} - {a['message']}")

        self.status_label.setText("Relink complete")

    def on_batch_clean(self):
        self.add_result("INFO", "Day 7: Batch wiring stub.")
        self.add_result("INFO", "Next: generate batch command + run batch_runner.py via 3dsmaxcmd.exe.")
        self.status_label.setText("Batch: stub (Day 7)")

    def on_batch_clean(self):
        from batch.batch_runner import run_batch

        input_dir = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Input Folder (contains .max files)")
        if not input_dir:
            self.add_result("INFO", "Batch canceled (no input folder).")
            return

        output_dir = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Output Folder (cleaned copies + reports)")
        if not output_dir:
            self.add_result("INFO", "Batch canceled (no output folder).")
            return

        self.status_label.setText("Batch cleaning...")
        self.add_result("INFO", f"Batch input: {input_dir}")
        self.add_result("INFO", f"Batch output: {output_dir}")

        options = self.get_options()
        try:
            summary_path = run_batch(input_dir, output_dir, options)
            self._last_reports_dir = os.path.dirname(summary_path)
            self.add_result("INFO", f"Batch complete. Summary: {summary_path}")
            self.status_label.setText("Batch complete")
        except Exception as e:
            self.add_result("ERROR", f"Batch failed: {e}")
            self.status_label.setText("Batch failed")


    def on_open_reports(self):
        import os
        import subprocess

        reports_dir = getattr(self, "_last_reports_dir", None)
        if not reports_dir or not os.path.isdir(reports_dir):
            self.add_result("WARNING", "No reports folder yet. Run a batch first.")
            return

        try:
            os.startfile(reports_dir)  # Windows
            self.add_result("INFO", f"Opened reports: {reports_dir}")
        except Exception:
            try:
                subprocess.Popen(["explorer", reports_dir])
            except Exception as e:
                self.add_result("ERROR", f"Could not open reports folder: {e}")


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


