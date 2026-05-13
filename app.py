import hashlib
import json
import os
import re
import sys

from collections import defaultdict
from pathlib import Path

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QListView
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from core.PluginManager import PluginManager


CONFIG_FILE = "gta5populator_config.json"


class Gta5Populator:
    def __init__(self):
        self.plugin_manager = PluginManager()
        self.paths = []
        self.categories = self.empty_categories()
        self.known_files = set()
        self.detected_files = []

        self.load_config()
        self.scan_files(initial=True)
        self.plugin_manager.hook("on_app_start", self)

    @property
    def context(self):
        # Compatibility shim: plugins often expect manager.context.
        return self.plugin_manager.context

    def aliases(self):
        # Compatibility shim for older plugins that call manager.aliases().
        return self.plugin_manager.aliases()

    def empty_categories(self):
        return {category: [] for category in self.plugin_manager.categories()}

    # =====================================================
    # CONFIG
    # =====================================================

    def load_config(self):
        if not Path(CONFIG_FILE).exists():
            return

        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.paths = [Path(x) for x in data.get("paths", [])]
            self.known_files = set(data.get("known_files", []))
            self.plugin_manager.hook("on_config_loaded", self, data)

        except Exception:
            self.paths = []
            self.known_files = set()

    def save_config(self):
        data = {
            "paths": [str(x) for x in self.paths],
            "known_files": sorted(self.known_files),
        }
        self.plugin_manager.hook("on_config_saving", self, data)

        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    # =====================================================
    # HELPERS
    # =====================================================

    def hash_file(self, path: Path):
        return hashlib.md5(str(path).encode()).hexdigest()

    def detect_category(self, path: Path):
        category = self.plugin_manager.first_result("detect_category", self, path)
        return category or "BaseGame"

    def clean_name(self, name: str):
        name = name.replace(".disabled", "")
        lowered = name.lower()

        plugin_name = self.plugin_manager.first_result("clean_bundle_name", self, name)

        if plugin_name:
            return plugin_name

        for key, value in self.plugin_manager.aliases().items():
            if lowered.startswith(key):
                return value

        cleaned = re.sub(r"(v?\d+)$", "", name, flags=re.IGNORECASE)
        cleaned = cleaned.replace("_", "")
        cleaned = cleaned.replace("-", "")

        return cleaned

    # =====================================================
    # FOLDER MANAGEMENT
    # =====================================================

    def add_folder(self, path: Path):
        if path not in self.paths:
            self.paths.append(path)

        self.save_config()
        self.plugin_manager.hook("on_folder_added", self, path)
        self.scan_files(initial=True)

    def remove_folder(self, path: Path):
        if path in self.paths:
            self.paths.remove(path)

        self.save_config()
        self.plugin_manager.hook("on_folder_removed", self, path)
        self.scan_files(initial=True)

    # =====================================================
    # FILE SCANNING
    # =====================================================

    def scan_files(self, initial=False):
        self.categories = self.empty_categories()

        grouped = {
            category: defaultdict(list)
            for category in self.plugin_manager.categories()
        }

        self.detected_files = []
        self.plugin_manager.hook("before_scan", self, initial)

        for directory in self.paths:
            if not directory.exists():
                continue

            for file in directory.rglob("*"):
                if not file.is_file():
                    continue

                is_disabled = file.suffix == ".disabled"
                actual_file = self.plugin_manager.first_result(
                    "normalize_file_path", self, file, is_disabled
                )

                if actual_file is None:
                    actual_file = file.with_suffix("") if is_disabled else file

                include_file = self.plugin_manager.first_result(
                    "should_include_file", self, file, actual_file
                )

                if include_file is False:
                    continue

                if include_file is None and actual_file.suffix.lower() not in self.plugin_manager.supported_extensions():
                    continue

                stem = actual_file.stem

                if stem.lower() in self.plugin_manager.ignored_stems():
                    continue

                file_hash = self.hash_file(file)

                if file_hash not in self.known_files and not initial:
                    self.detected_files.append(file)
                    self.plugin_manager.hook("on_new_file_detected", self, file)

                self.known_files.add(file_hash)

                category = self.detect_category(file)
                grouped.setdefault(category, defaultdict(list))
                self.categories.setdefault(category, [])
                parent_name = file.parent.name

                plugin_bundle_name = self.plugin_manager.first_result(
                    "get_bundle_name", self, file, actual_file, category
                )

                if plugin_bundle_name:
                    bundle_name = plugin_bundle_name
                elif parent_name.lower() not in self.plugin_manager.ignored_parent_names():
                    bundle_name = parent_name
                else:
                    bundle_name = self.clean_name(stem)

                file_data = {
                    "path": file,
                    "active": not is_disabled,
                    "disabled": is_disabled,
                }

                grouped[category][bundle_name].append(file_data)
                self.plugin_manager.hook(
                    "on_file_grouped", self, file, category, bundle_name, file_data
                )

        self.save_config()

        for category, bundles in grouped.items():
            final_bundles = []

            for bundle_name, files in bundles.items():
                active = any(x["active"] for x in files)

                final_bundles.append(
                    {
                        "name": bundle_name,
                        "files": files,
                        "active": active,
                    }
                )
                self.plugin_manager.hook(
                    "after_bundle_built", self, category, final_bundles[-1]
                )

            final_bundles.sort(key=lambda x: x["name"].lower())
            self.categories[category] = final_bundles

        self.plugin_manager.hook("after_scan", self, initial, grouped)

    # =====================================================
    # TOGGLE
    # =====================================================

    def toggle_bundle(self, bundle):
        currently_active = bundle["active"]
        enabling = currently_active is False
        self.plugin_manager.hook("before_toggle_bundle", self, bundle, enabling)

        for file_data in bundle["files"]:
            file_path = file_data["path"]
            self.plugin_manager.hook("before_toggle_file", self, file_path, enabling)

            if currently_active:
                new_path = file_path.with_name(file_path.name + ".disabled")
            else:
                new_path = file_path.with_name(file_path.name.replace(".disabled", ""))

            os.rename(file_path, new_path)
            self.plugin_manager.hook("after_toggle_file", self, file_path, new_path, enabling)

        self.plugin_manager.hook("after_toggle_bundle", self, bundle, enabling)
        self.scan_files()

    def disable_file(self, path: Path):
        if path.name.endswith(".disabled"):
            return

        new_path = path.with_name(path.name + ".disabled")
        self.plugin_manager.hook("before_disable_file", self, path)
        os.rename(path, new_path)
        self.plugin_manager.hook("after_disable_file", self, path, new_path)
        self.scan_files()


class Gta5PopulatorWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.manager = Gta5Populator()
        self.current_bundles = []
        self.filtered_bundles = []
        self.plugin_debugger = None

        self.setWindowTitle("GTA V Mod Manager")
        self.resize(1060, 780)
        self.setMinimumSize(880, 640)

        self.build_ui()
        self.apply_theme()
        self.refresh_ui()
        self.manager.plugin_manager.hook("on_ui_ready", self.manager, self)

    def build_ui(self):
        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(14, 12, 14, 10)
        root_layout.setSpacing(8)

        header = QHBoxLayout()
        title_area = QVBoxLayout()

        title = QLabel("GTA V MOD MANAGER")
        title.setObjectName("Title")

        extensions = ", ".join(sorted(self.manager.plugin_manager.supported_extensions()))
        self.subtitle = QLabel(f"Manage {extensions} mods from your GTA V folders.")
        self.subtitle.setObjectName("Subtitle")

        title_area.addWidget(title)
        title_area.addWidget(self.subtitle)

        header.addLayout(title_area)
        header.addStretch(1)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setObjectName("SecondaryButton")
        self.refresh_button.clicked.connect(self.refresh_scan)

        self.debug_button = QPushButton("Debug")
        self.debug_button.setObjectName("SecondaryButton")
        self.debug_button.clicked.connect(self.open_plugin_debugger)

        header.addWidget(self.debug_button)
        header.addWidget(self.refresh_button)

        root_layout.addLayout(header)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        mod_panel = self.create_mod_panel()
        side_panel = QWidget()
        side_layout = QVBoxLayout(side_panel)
        side_layout.setContentsMargins(0, 0, 0, 0)
        side_layout.setSpacing(8)
        side_layout.addWidget(self.create_folder_panel(), 1)
        side_layout.addWidget(self.create_detect_panel(), 1)

        splitter.addWidget(mod_panel)
        splitter.addWidget(side_panel)
        splitter.setSizes([780, 260])

        root_layout.addWidget(splitter, 1)

        self.status_label = QLabel()
        self.status_label.setObjectName("Status")
        root_layout.addWidget(self.status_label)

        self.setCentralWidget(root)

    def create_folder_panel(self):
        panel = QGroupBox("Folders")
        layout = QVBoxLayout(panel)
        layout.setSpacing(8)

        self.folder_list = QListWidget()
        self.folder_list.setObjectName("FolderList")
        self.folder_list.setSelectionMode(QListWidget.SingleSelection)
        layout.addWidget(self.folder_list, 1)

        buttons = QHBoxLayout()
        buttons.setSpacing(8)

        self.add_folder_button = QPushButton("Add Folder")
        self.add_folder_button.clicked.connect(self.add_folder)
        buttons.addWidget(self.add_folder_button)

        self.remove_folder_button = QPushButton("Remove Selected")
        self.remove_folder_button.clicked.connect(self.remove_folder)
        buttons.addWidget(self.remove_folder_button)

        layout.addLayout(buttons)

        return panel

    def create_mod_panel(self):
        panel = QGroupBox("Manage Mods")
        layout = QVBoxLayout(panel)
        layout.setSpacing(8)

        controls = QHBoxLayout()
        controls.setSpacing(12)

        category_label = QLabel("Category")
        self.category_combo = QComboBox()
        self.category_combo.currentIndexChanged.connect(self.on_category_changed)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search mods...")
        self.search_box.textChanged.connect(self.refresh_bundle_list)

        controls.addWidget(category_label)
        controls.addWidget(self.category_combo, 1)
        controls.addWidget(self.search_box, 2)

        layout.addLayout(controls)

        content = QSplitter(Qt.Horizontal)
        content.setChildrenCollapsible(False)

        browser = QWidget()
        browser_layout = QVBoxLayout(browser)
        browser_layout.setContentsMargins(0, 0, 0, 0)
        browser_layout.setSpacing(8)

        self.mod_count_label = QLabel()
        self.mod_count_label.setObjectName("PanelHint")
        browser_layout.addWidget(self.mod_count_label)

        self.bundle_list = QListWidget()
        self.bundle_list.setObjectName("BundleList")
        self.bundle_list.setSelectionMode(QListWidget.SingleSelection)
        self.bundle_list.setUniformItemSizes(True)
        self.bundle_list.setLayoutMode(QListView.Batched)
        self.bundle_list.setBatchSize(40)
        self.bundle_list.currentItemChanged.connect(self.on_bundle_selected)
        self.bundle_list.itemDoubleClicked.connect(self.on_bundle_double_clicked)
        browser_layout.addWidget(self.bundle_list, 1)

        details = QWidget()
        details.setObjectName("DetailsPane")
        details_layout = QVBoxLayout(details)
        details_layout.setContentsMargins(12, 0, 0, 0)
        details_layout.setSpacing(8)

        self.bundle_title = QLabel("Select a mod")
        self.bundle_title.setObjectName("BundleTitle")

        self.bundle_summary = QLabel("Choose a mod from the list to see its files.")
        self.bundle_summary.setObjectName("BundleSummary")
        self.bundle_summary.setWordWrap(True)

        details_layout.addWidget(self.bundle_title)
        details_layout.addWidget(self.bundle_summary)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setObjectName("Divider")
        details_layout.addWidget(line)

        files_label = QLabel("Files in selected mod")
        files_label.setObjectName("PanelHint")
        details_layout.addWidget(files_label)

        self.file_list = QListWidget()
        self.file_list.setObjectName("FileList")
        self.file_list.setUniformItemSizes(True)
        self.file_list.itemDoubleClicked.connect(self.on_file_double_clicked)
        details_layout.addWidget(self.file_list, 1)

        self.toggle_button = QPushButton("Enable / Disable Bundle")
        self.toggle_button.clicked.connect(self.toggle_current_bundle)
        details_layout.addWidget(self.toggle_button)

        content.addWidget(browser)
        content.addWidget(details)
        content.setSizes([560, 210])

        layout.addWidget(content, 1)

        return panel

    def create_detect_panel(self):
        panel = QGroupBox("New Files")
        layout = QVBoxLayout(panel)
        layout.setSpacing(8)

        self.detect_button = QPushButton("Detect New Files")
        self.detect_button.setObjectName("SecondaryButton")
        self.detect_button.clicked.connect(self.detect_new_files)
        layout.addWidget(self.detect_button)

        self.detected_list = QListWidget()
        self.detected_list.setSelectionMode(QListWidget.SingleSelection)
        layout.addWidget(self.detected_list, 1)

        buttons = QHBoxLayout()
        buttons.setSpacing(8)

        self.disable_detected_button = QPushButton("Disable Selected")
        self.disable_detected_button.clicked.connect(self.disable_detected_file)
        buttons.addWidget(self.disable_detected_button)

        self.ignore_detected_button = QPushButton("Ignore Selected")
        self.ignore_detected_button.clicked.connect(self.ignore_detected_file)
        buttons.addWidget(self.ignore_detected_button)

        layout.addLayout(buttons)

        return panel

    def apply_theme(self):
        self.setStyleSheet(
            """
            QWidget {
                background: #000000;
                color: #f4f4f4;
                font-family: Segoe UI, Arial, sans-serif;
                font-size: 12px;
            }

            QMainWindow {
                background: #000000;
            }

            QLabel#Title {
                color: #ffffff;
                font-size: 22px;
                font-weight: 800;
                letter-spacing: 0;
            }

            QLabel#Subtitle,
            QLabel#Status,
            QLabel#BundleSummary,
            QLabel#PanelHint {
                color: #a9a9a9;
            }

            QLabel#BundleTitle {
                color: #ffffff;
                font-size: 17px;
                font-weight: 800;
            }

            QLabel#Status {
                padding: 2px;
            }

            QGroupBox {
                border: 1px solid #222222;
                border-radius: 8px;
                margin-top: 14px;
                padding: 13px 10px 10px 10px;
                background: #050505;
                font-weight: 700;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                color: #ffffff;
            }

            QLineEdit,
            QListWidget,
            QComboBox {
                background: #0a0a0a;
                border: 1px solid #242424;
                border-radius: 6px;
                color: #ffffff;
                padding: 7px;
                selection-background-color: #ffffff;
                selection-color: #000000;
            }

            QLineEdit {
                min-height: 20px;
            }

            QListWidget::item {
                padding: 4px 8px;
                border-radius: 4px;
            }

            QListWidget#BundleList::item {
                min-height: 24px;
            }

            QListWidget#FileList::item,
            QListWidget#FolderList::item {
                min-height: 22px;
            }

            QListWidget::item:selected {
                background: #ffffff;
                color: #000000;
            }

            QComboBox::drop-down {
                border: 0;
                width: 28px;
            }

            QComboBox QAbstractItemView {
                background: #080808;
                border: 1px solid #303030;
                color: #ffffff;
                selection-background-color: #ffffff;
                selection-color: #000000;
                outline: 0;
            }

            QPushButton {
                background: #ffffff;
                border: 1px solid #ffffff;
                border-radius: 6px;
                color: #000000;
                font-weight: 700;
                min-height: 30px;
                padding: 7px 12px;
            }

            QWidget#DetailsPane {
                border-left: 1px solid #181818;
            }

            QPushButton#SecondaryButton {
                background: #121212;
                border-color: #303030;
                color: #ffffff;
            }

            QPushButton#SecondaryButton:hover {
                background: #1f1f1f;
                border-color: #474747;
            }

            QPushButton:hover {
                background: #dcdcdc;
                border-color: #dcdcdc;
            }

            QPushButton:pressed {
                background: #bdbdbd;
                border-color: #bdbdbd;
            }

            QPushButton:disabled {
                background: #151515;
                border-color: #242424;
                color: #666666;
            }

            QFrame#Divider {
                color: #222222;
                background: #222222;
                max-height: 1px;
            }

            QSplitter::handle {
                background: #111111;
            }
            """
        )

    def refresh_ui(self, keep_category=None, keep_bundle=None):
        current_category = keep_category or self.category_combo.currentData()
        current_bundle_name = keep_bundle or self.current_bundle_name()

        self.refresh_folder_list()
        self.refresh_category_combo(current_category)
        self.refresh_bundle_list(current_bundle_name)
        self.refresh_detected_list()
        self.update_status()
        self.manager.plugin_manager.hook("on_ui_refreshed", self.manager, self)

    def refresh_folder_list(self):
        self.folder_list.clear()

        for path in self.manager.paths:
            item = QListWidgetItem(str(path))
            item.setData(Qt.UserRole, path)
            self.folder_list.addItem(item)

        self.remove_folder_button.setEnabled(bool(self.manager.paths))

    def refresh_category_combo(self, selected_category=None):
        self.category_combo.blockSignals(True)
        self.category_combo.clear()

        for category in self.manager.categories:
            bundles = self.manager.categories[category]
            label = f"{category} ({len(bundles)})"
            self.category_combo.addItem(label, category)

        index = self.category_combo.findData(selected_category)

        if index < 0:
            index = 0

        self.category_combo.setCurrentIndex(index)
        self.category_combo.blockSignals(False)

    def refresh_bundle_list(self, selected_bundle_name=None):
        category = self.category_combo.currentData()
        self.current_bundles = self.manager.categories.get(category, [])
        search = self.search_box.text().strip().lower()

        if search:
            self.filtered_bundles = [
                bundle
                for bundle in self.current_bundles
                if search in bundle["name"].lower()
                or any(search in str(file_data["path"]).lower() for file_data in bundle["files"])
            ]
        else:
            self.filtered_bundles = list(self.current_bundles)

        previous_name = selected_bundle_name or self.current_bundle_name()

        self.bundle_list.blockSignals(True)
        self.bundle_list.clear()

        for bundle in self.filtered_bundles:
            status = "Enabled" if bundle["active"] else "Disabled"
            file_count = len(bundle["files"])
            marker = "[ON]" if bundle["active"] else "[OFF]"
            default_text = f"{marker}  {bundle['name']}    {status}    {file_count} file(s)"
            row_text = self.manager.plugin_manager.first_result(
                "format_bundle_row", self.manager, bundle, default_text
            )
            display_text, row_fg, row_bg = self.normalize_row_output(
                row_text, default_text
            )
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, bundle["name"])
            item.setSizeHint(QSize(0, 28))
            self.apply_item_colors(
                item,
                self.manager.plugin_manager.first_result(
                    "bundle_color", self.manager, bundle
                ),
            )
            self.apply_item_colors(item, {"fg": row_fg, "bg": row_bg})
            self.bundle_list.addItem(item)

        selected_row = 0

        if previous_name:
            for row, bundle in enumerate(self.filtered_bundles):
                if bundle["name"] == previous_name:
                    selected_row = row
                    break

        if self.filtered_bundles:
            self.bundle_list.setCurrentRow(selected_row)

        self.bundle_list.blockSignals(False)
        self.mod_count_label.setText(
            f"{len(self.filtered_bundles)} shown from {len(self.current_bundles)} mod(s)"
        )
        self.on_bundle_selected()

    def refresh_detected_list(self):
        self.detected_list.clear()

        for path in self.manager.detected_files:
            item = QListWidgetItem(str(path))
            item.setData(Qt.UserRole, path)
            self.detected_list.addItem(item)

        has_detected = bool(self.manager.detected_files)
        self.disable_detected_button.setEnabled(has_detected)
        self.ignore_detected_button.setEnabled(has_detected)

    def on_category_changed(self):
        self.refresh_bundle_list()
        self.update_status()

    def on_bundle_selected(self):
        bundle = self.current_bundle()
        self.file_list.clear()

        if not bundle:
            self.bundle_title.setText("No mod selected")
            self.bundle_summary.setText("No mods found in this category.")
            self.toggle_button.setEnabled(False)
            return

        status = "enabled" if bundle["active"] else "disabled"

        default_description = (
            f"This mod is currently {status}. "
            f"{len(bundle['files'])} file(s) are part of this bundle."
        )

        info = self.manager.plugin_manager.first_result(
            "get_bundle_info",
            self.manager,
            bundle,
        )

        description = default_description

        if info:
            description = info.get("description", default_description)

        self.bundle_title.setText(bundle["name"])
        self.bundle_summary.setText(description)

        for file_data in bundle["files"]:
            file_path = file_data["path"]
            file_status = "Enabled" if file_data["active"] else "Disabled"
            default_text = f"{file_path.name} [{file_status}]"
            row_text = self.manager.plugin_manager.first_result(
                "format_file_row", self.manager, file_data, default_text
            )
            display_text, row_fg, row_bg = self.normalize_row_output(
                row_text, default_text
            )
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, file_data)
            item.setToolTip(str(file_path))
            item.setSizeHint(QSize(0, 26))
            self.apply_item_colors(
                item,
                self.manager.plugin_manager.first_result(
                    "file_color", self.manager, file_data
                ),
            )
            self.apply_item_colors(item, {"fg": row_fg, "bg": row_bg})
            self.file_list.addItem(item)

        action = "Disable Bundle" if bundle["active"] else "Enable Bundle"
        self.toggle_button.setText(action)
        self.toggle_button.setEnabled(True)
        self.manager.plugin_manager.hook("on_bundle_selected", self.manager, bundle)

    def on_bundle_double_clicked(self, item):
        bundle_name = item.data(Qt.UserRole)

        for bundle in self.filtered_bundles:
            if bundle["name"] == bundle_name:
                self.manager.plugin_manager.hook("on_bundle_double_click", self.manager, bundle)
                return

    def on_file_double_clicked(self, item):
        file_data = item.data(Qt.UserRole)

        if file_data:
            self.manager.plugin_manager.hook("on_file_double_click", self.manager, file_data)

    def current_bundle_name(self):
        item = self.bundle_list.currentItem()

        if not item:
            return None

        return item.data(Qt.UserRole)

    def current_bundle(self):
        bundle_name = self.current_bundle_name()

        for bundle in self.filtered_bundles:
            if bundle["name"] == bundle_name:
                return bundle

        return None

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select GTA V Folder")

        if not folder:
            return

        self.manager.add_folder(Path(folder))
        self.refresh_ui()
        self.show_message(f"Added folder: {folder}")

    def remove_folder(self):
        item = self.folder_list.currentItem()

        if not item:
            QMessageBox.information(self, "Remove Folder", "Select a folder first.")
            return

        path = item.data(Qt.UserRole)

        answer = QMessageBox.question(
            self,
            "Remove Folder",
            f"Remove this folder from the manager?\n\n{path}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        self.manager.remove_folder(path)
        self.refresh_ui()
        self.show_message(f"Removed folder: {path}")

    def refresh_scan(self):
        category = self.category_combo.currentData()
        bundle = self.current_bundle_name()

        self.manager.scan_files()
        self.refresh_ui(category, bundle)
        self.show_message("Scan complete.")

    def toggle_current_bundle(self):
        bundle = self.current_bundle()

        if not bundle:
            return

        category = self.category_combo.currentData()
        bundle_name = bundle["name"]

        try:
            self.manager.toggle_bundle(bundle)
        except OSError as exc:
            QMessageBox.critical(self, "Toggle Bundle", f"Could not rename one of the files.\n\n{exc}")
            self.manager.scan_files()

        self.refresh_ui(category, bundle_name)
        self.show_message(f"Updated bundle: {bundle_name}")

    def detect_new_files(self):
        category = self.category_combo.currentData()
        bundle = self.current_bundle_name()

        self.manager.scan_files()
        self.refresh_ui(category, bundle)

        count = len(self.manager.detected_files)
        if count:
            self.show_message(f"Detected {count} new file(s).")
        else:
            self.show_message("No newly detected files.")

    def disable_detected_file(self):
        item = self.detected_list.currentItem()

        if not item:
            QMessageBox.information(self, "Disable File", "Select a detected file first.")
            return

        path = item.data(Qt.UserRole)

        try:
            self.manager.disable_file(path)
        except OSError as exc:
            QMessageBox.critical(self, "Disable File", f"Could not disable the file.\n\n{exc}")
            self.manager.scan_files()
            self.refresh_ui()
            return

        self.manager.detected_files = [x for x in self.manager.detected_files if x != path]
        self.refresh_ui()
        self.show_message(f"Disabled file: {path.name}")

    def ignore_detected_file(self):
        item = self.detected_list.currentItem()

        if not item:
            QMessageBox.information(self, "Ignore File", "Select a detected file first.")
            return

        path = item.data(Qt.UserRole)
        self.manager.detected_files = [x for x in self.manager.detected_files if x != path]
        self.refresh_detected_list()
        self.update_status()
        self.show_message(f"Ignored file: {path.name}")

    def update_status(self):
        folder_count = len(self.manager.paths)
        bundle_count = sum(len(bundles) for bundles in self.manager.categories.values())
        detected_count = len(self.manager.detected_files)
        default_text = (
            f"{folder_count} folder(s) | {bundle_count} bundle(s) | "
            f"{detected_count} newly detected file(s)"
        )

        self.status_label.setText(
            self.manager.plugin_manager.first_result(
                "format_status", self.manager, default_text
            )
            or default_text
        )

    def show_message(self, message):
        self.status_label.setText(message)

    def open_plugin_debugger(self):
        from core.debug.PluginDebugger import PluginDebuggerWindow

        if self.plugin_debugger is None:
            self.plugin_debugger = PluginDebuggerWindow(parent=self)

        self.plugin_debugger.show()
        self.plugin_debugger.raise_()
        self.plugin_debugger.activateWindow()

    def apply_item_colors(self, item, color_spec):
        if not color_spec:
            return

        fg = None
        bg = None

        if isinstance(color_spec, str):
            fg = color_spec
        elif isinstance(color_spec, (tuple, list)):
            if len(color_spec) > 0:
                fg = color_spec[0]
            if len(color_spec) > 1:
                bg = color_spec[1]
        elif isinstance(color_spec, dict):
            fg = color_spec.get("fg")
            bg = color_spec.get("bg")

        if fg:
            qfg = QColor(str(fg))
            if qfg.isValid():
                item.setForeground(qfg)

        if bg:
            qbg = QColor(str(bg))
            if qbg.isValid():
                item.setBackground(qbg)

    def normalize_row_output(self, plugin_value, default_text):
        if plugin_value is None:
            return default_text, None, None

        if isinstance(plugin_value, str):
            return plugin_value, None, None

        if isinstance(plugin_value, dict):
            text = str(plugin_value.get("text", default_text))
            fg = plugin_value.get("fg") or plugin_value.get("color")
            bg = plugin_value.get("bg") or plugin_value.get("background")
            return text, fg, bg

        if isinstance(plugin_value, (list, tuple)):
            if not plugin_value:
                return default_text, None, None

            text = str(plugin_value[0]) if plugin_value[0] is not None else default_text
            fg = plugin_value[1] if len(plugin_value) > 1 else None
            bg = plugin_value[2] if len(plugin_value) > 2 else None
            return text, fg, bg

        return str(plugin_value), None, None


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("GTA V Mod Manager")

    window = Gta5PopulatorWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
