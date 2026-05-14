import sys
from pathlib import Path
from pprint import pformat

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QBrush
from PyQt5.QtWidgets import *

from core.PluginManager import PluginManager
from core.plugin_hook_registry import (
    DECLARED_HOOK_NAMES,
    EXTENSION_AREAS,
    EXTENSION_PHASES,
    FIRST_RESULT_HOOKS,
    discover_bootstrap_pipeline_methods,
)


class MockApp:
    def __init__(self, pm):
        self.plugin_manager = pm
        self.context = pm.context
        self.paths = [Path("mock/GTA V")]
        self.categories = {
            "BaseGame": [],
            "Scripts": [],
        }
        self.known_files = set()
        self.detected_files = []

    def aliases(self):
        return self.plugin_manager.aliases()


class FastBug(QMainWindow):
    def __init__(self):
        super().__init__()

        self.pm = None
        self.mock = None
        self.plugins_by_row = []

        self.setWindowTitle("FASTBUG")
        self.resize(1400, 820)
        self.setMinimumSize(900, 520)

        self.build_ui()
        self.apply_theme()
        self.reload_plugins()

    # =========================================================
    # UI
    # =========================================================

    def build_ui(self):
        root = QWidget()

        self.setCentralWidget(root)

        layout = QVBoxLayout(root)

        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        # =====================================================
        # HEADER
        # =====================================================

        top = QHBoxLayout()

        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(8)

        title = QLabel("FASTBUG")
        title.setObjectName("Title")

        subtitle = QLabel(
            "plugin runtime debugger"
        )
        subtitle.setObjectName("Subtitle")

        top.addWidget(title)
        top.addWidget(subtitle)
        top.addStretch(1)

        layout.addLayout(top)

        # =====================================================
        # TOOLBAR
        # =====================================================

        toolbar = QToolBar()

        toolbar.setMovable(False)
        toolbar.setFloatable(False)

        self.addToolBar(toolbar)

        self.hook_combo = QComboBox()
        self.hook_combo.setMinimumWidth(260)

        self.area_combo = QComboBox()
        self.area_combo.addItems(
            EXTENSION_AREAS
        )

        self.phase_combo = QComboBox()
        self.phase_combo.addItems(
            EXTENSION_PHASES
        )

        self.pipeline_combo = QComboBox()
        self.pipeline_combo.setMinimumWidth(120)

        run_btn = QPushButton("RUN")
        run_btn.clicked.connect(
            self.run_hook
        )

        pipe_btn = QPushButton("PIPE")
        pipe_btn.clicked.connect(
            self.run_pipeline
        )

        reload_btn = QPushButton("RELOAD")
        reload_btn.clicked.connect(
            self.reload_plugins
        )

        toolbar.addWidget(QLabel("hook"))
        toolbar.addWidget(self.hook_combo)

        toolbar.addSeparator()

        toolbar.addWidget(QLabel("ext"))
        toolbar.addWidget(self.area_combo)
        toolbar.addWidget(self.phase_combo)

        toolbar.addSeparator()

        toolbar.addWidget(QLabel("pipeline"))
        toolbar.addWidget(self.pipeline_combo)

        toolbar.addSeparator()

        toolbar.addWidget(run_btn)
        toolbar.addWidget(pipe_btn)
        toolbar.addWidget(reload_btn)

        # =====================================================
        # MAIN
        # =====================================================

        outer = QSplitter(Qt.Horizontal)

        # =====================================================
        # LEFT
        # =====================================================

        left = QWidget()

        ll = QVBoxLayout(left)

        ll.setContentsMargins(0, 0, 0, 0)
        ll.setSpacing(2)

        left_label = QLabel("plugins")
        left_label.setObjectName("Section")

        self.plugin_list = QListWidget()

        self.plugin_list.setSpacing(0)

        self.plugin_list.currentRowChanged.connect(
            self.refresh_plugin_detail
        )

        ll.addWidget(left_label)
        ll.addWidget(self.plugin_list)

        # =====================================================
        # CENTER
        # =====================================================

        center = QWidget()

        cl = QVBoxLayout(center)

        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(2)

        self.tabs = QTabWidget()

        self.overview = QTextEdit()
        self.overview.setReadOnly(True)

        self.data = QTextEdit()
        self.data.setReadOnly(True)

        self.hooks = QListWidget()
        self.hooks.setSpacing(0)

        self.coverage = QTableWidget(0, 4)

        self.coverage.setHorizontalHeaderLabels(
            [
                "hook",
                "plugin",
                "callback",
                "layer",
            ]
        )

        hh = self.coverage.horizontalHeader()

        hh.setStretchLastSection(False)

        hh.setSectionResizeMode(
            0,
            QHeaderView.Stretch,
        )

        hh.setSectionResizeMode(
            1,
            QHeaderView.Stretch,
        )

        hh.setSectionResizeMode(
            2,
            QHeaderView.ResizeToContents,
        )

        hh.setSectionResizeMode(
            3,
            QHeaderView.ResizeToContents,
        )

        self.tabs.addTab(
            self.overview,
            "overview",
        )

        self.tabs.addTab(
            self.data,
            "data",
        )

        self.tabs.addTab(
            self.hooks,
            "hooks",
        )

        self.tabs.addTab(
            self.coverage,
            "coverage",
        )

        cl.addWidget(self.tabs)

        # =====================================================
        # RIGHT
        # =====================================================

        right = QWidget()

        rl = QVBoxLayout(right)

        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(2)

        self.output_tabs = QTabWidget()

        self.events = QTextEdit()
        self.events.setReadOnly(True)

        self.errors = QTextEdit()
        self.errors.setReadOnly(True)

        self.context = QTextEdit()
        self.context.setReadOnly(True)

        self.runtime = QTextEdit()
        self.runtime.setReadOnly(True)

        self.output_tabs.addTab(
            self.events,
            "events",
        )

        self.output_tabs.addTab(
            self.errors,
            "errors",
        )

        self.output_tabs.addTab(
            self.context,
            "context",
        )

        self.output_tabs.addTab(
            self.runtime,
            "runtime",
        )

        rl.addWidget(self.output_tabs)

        # =====================================================
        # SPLITTER
        # =====================================================

        outer.addWidget(left)
        outer.addWidget(center)
        outer.addWidget(right)

        outer.setSizes([
            220,
            420,
            760,
        ])

        outer.setStretchFactor(0, 0)
        outer.setStretchFactor(1, 1)
        outer.setStretchFactor(2, 2)

        layout.addWidget(outer)

        # =====================================================
        # STATUS
        # =====================================================

        self.status = QLabel("ready")
        self.status.setObjectName("Status")

        layout.addWidget(self.status)

    # =========================================================
    # THEME
    # =========================================================

    def apply_theme(self):
        self.setStyleSheet("""
        QWidget {
            background:#000000;
            color:#cfcfcf;
            font-family:Consolas;
            font-size:11px;
        }

        QMainWindow {
            background:#000000;
        }

        QLabel#Title {
            color:#ffffff;
            font-size:14px;
            font-weight:700;
        }

        QLabel#Subtitle {
            color:#555555;
            font-size:11px;
        }

        QLabel#Section {
            color:#777777;
            font-size:10px;
        }

        QLabel#Status {
            color:#666666;
            border-top:1px solid #111111;
            padding-top:2px;
        }

        QListWidget,
        QTextEdit,
        QTableWidget,
        QComboBox {
            background:#000000;
            border:1px solid #222222;
            color:#d8d8d8;
        }

        QTextEdit {
            padding:4px;
        }

        QListWidget::item {
            padding:1px 3px;
            margin:0;
            border:none;
        }

        QListWidget::item:selected {
            background:#101010;
            border:1px solid #444444;
        }

        QHeaderView::section {
            background:#080808;
            color:#777777;
            border:1px solid #222222;
            padding:2px;
        }

        QPushButton {
            background:#050505;
            border:1px solid #333333;
            padding:2px 8px;
            font-weight:700;
            min-height:18px;
        }

        QPushButton:hover {
            background:#101010;
        }

        QToolBar {
            border-top:1px solid #111111;
            border-bottom:1px solid #111111;
            spacing:2px;
            padding:1px;
        }

        QTabWidget::pane {
            border:1px solid #222222;
            margin-top:-1px;
        }

        QTabBar::tab {
            background:#000000;
            border:1px solid #222222;
            padding:3px 8px;
            margin-right:1px;
            color:#666666;
        }

        QTabBar::tab:selected {
            background:#080808;
            color:#ffffff;
        }

        QSplitter::handle {
            background:#111111;
        }

        QScrollBar:vertical {
            background:#050505;
            width:8px;
        }

        QScrollBar::handle:vertical {
            background:#333333;
            min-height:20px;
        }

        QScrollBar:horizontal {
            background:#050505;
            height:8px;
        }

        QScrollBar::handle:horizontal {
            background:#333333;
            min-width:20px;
        }
        """)

    # =========================================================
    # RELOAD
    # =========================================================

    def reload_plugins(self):
        self.pm = PluginManager("plugins")

        self.mock = MockApp(self.pm)

        self.pm.hook(
            "on_app_start",
            self.mock,
        )

        self.refresh_hook_combo()
        self.refresh_pipeline_combo()
        self.refresh_plugins()
        self.refresh_logs()
        self.refresh_runtime()
        self.refresh_coverage()

        self.status.setText(
            f"{len(self.pm.plugins)} plugins loaded"
        )

    # =========================================================
    # HOOKS
    # =========================================================

    def available_hooks(self):
        names = set(
            DECLARED_HOOK_NAMES
        )

        for plugin in self.pm.plugins:

            for pipeline in discover_bootstrap_pipeline_methods(plugin):

                names.add(
                    f"bootstrap_pipeline::{pipeline}"
                )

        return sorted(names)

    def refresh_hook_combo(self):
        self.hook_combo.clear()

        self.hook_combo.addItems(
            self.available_hooks()
        )

    def refresh_pipeline_combo(self):
        self.pipeline_combo.clear()

        names = set()

        for plugin in self.pm.plugins:

            names.update(
                discover_bootstrap_pipeline_methods(plugin)
            )

        if not names:
            names.add("permission")

        self.pipeline_combo.addItems(
            sorted(names)
        )

    # =========================================================
    # PLUGINS
    # =========================================================

    def refresh_plugins(self):
        self.plugin_list.clear()

        self.plugins_by_row = self.pm.plugins

        for plugin in self.pm.plugins:

            name = getattr(
                plugin,
                "name",
                plugin.__class__.__name__,
            )

            priority = getattr(
                plugin,
                "priority",
                0,
            )

            item = QListWidgetItem(
                f"{priority:>4} | {name}"
            )

            self.plugin_list.addItem(item)

        if self.pm.plugins:
            self.plugin_list.setCurrentRow(0)

    def refresh_plugin_detail(self):
        row = self.plugin_list.currentRow()

        if row < 0:
            return

        if row >= len(self.plugins_by_row):
            return

        plugin = self.plugins_by_row[row]

        report = getattr(
            plugin,
            "__plugin_permission_report__",
            {},
        )

        perms = ", ".join(
            report.get("permissions", [])
        )

        overview = [
            f"[NAME]        {getattr(plugin, 'name', '')}",
            f"[VERSION]     {getattr(plugin, 'version', '')}",
            f"[AUTHOR]      {getattr(plugin, 'author', '')}",
            f"[PRIORITY]    {getattr(plugin, 'priority', '')}",
            f"[FILE]        {getattr(plugin, '__plugin_file__', '')}",
            f"[DESC]        {getattr(plugin, 'description', '')}",
            "",
            f"[DANGEROUS]   {report.get('dangerous')}",
            f"[SCORE]       {report.get('score', 0)}",
            f"[PERMISSIONS] {perms}",
        ]

        self.overview.setPlainText(
            "\n".join(overview)
        )

        pdata = {
            "extensions":
                list(
                    getattr(
                        plugin,
                        "supported_extensions",
                        [],
                    )
                ),

            "aliases":
                getattr(
                    plugin,
                    "aliases",
                    {},
                ),

            "categories":
                getattr(
                    plugin,
                    "categories",
                    [],
                ),
        }

        self.data.setPlainText(
            pformat(
                pdata,
                width=48,
                compact=True,
            )
        )

        self.hooks.clear()

        for name in dir(type(plugin)):

            if not name.endswith((
                "_hook",
                "_process",
                "_core",
                "_internal",
            )):
                continue

            item = QListWidgetItem(name)

            if name.endswith("_hook"):

                item.setForeground(
                    QColor("#7fbfff")
                )

            elif name.endswith("_process"):

                item.setForeground(
                    QColor("#7fff9f")
                )

            elif name.endswith("_core"):

                item.setForeground(
                    QColor("#ffd56f")
                )

            elif name.endswith("_internal"):

                item.setForeground(
                    QColor("#ff9f80")
                )

            self.hooks.addItem(item)

    # =========================================================
    # COVERAGE
    # =========================================================

    def refresh_coverage(self):
        rows = []

        for hook in self.available_hooks():

            if hook.startswith(
                "bootstrap_pipeline::"
            ):
                continue

            callbacks = self.pm.callback_names(
                hook
            )

            for callback_name in callbacks:

                for plugin in self.pm.plugins:

                    callback = getattr(
                        plugin,
                        callback_name,
                        None,
                    )

                    if not callable(callback):
                        continue

                    rows.append([
                        hook,
                        getattr(plugin, "name", ""),
                        callback_name,
                        self.layer(callback_name),
                    ])

        self.coverage.setRowCount(
            len(rows)
        )

        for r, values in enumerate(rows):

            for c, value in enumerate(values):

                item = QTableWidgetItem(
                    str(value)
                )

                layer = values[3]

                if layer == "hook":

                    item.setForeground(
                        QBrush(
                            QColor("#7fbfff")
                        )
                    )

                elif layer == "process":

                    item.setForeground(
                        QBrush(
                            QColor("#7fff9f")
                        )
                    )

                elif layer == "core":

                    item.setForeground(
                        QBrush(
                            QColor("#ffd56f")
                        )
                    )

                elif layer == "internal":

                    item.setForeground(
                        QBrush(
                            QColor("#ff9f80")
                        )
                    )

                self.coverage.setItem(
                    r,
                    c,
                    item,
                )

    def layer(self, name):
        for suffix in (
            "_hook",
            "_process",
            "_core",
            "_internal",
        ):

            if name.endswith(suffix):
                return suffix[1:]

        return "base"

    # =========================================================
    # LOGS
    # =========================================================

    def refresh_logs(self):
        ev = []

        for i, e in enumerate(self.pm.event_log):

            code = e.get("code", "")

            msg = e.get("message", "")

            ev.append(
                f"{i:04X} | "
                f"{code:<28} | "
                f"{msg}"
            )

        self.events.setPlainText(
            "\n".join(ev)
        )

        er = []

        for e in self.pm.errors:

            er.append(
                "[ERR]\n"
                f"PLUGIN : {e.get('plugin')}\n"
                f"HOOK   : {e.get('hook')}\n"
                f"ERROR  : {e.get('error')}\n"
            )

        self.errors.setPlainText(
            "\n".join(er)
        )

        self.context.setPlainText(
            pformat(
                self.pm.context,
                width=52,
                compact=True,
            )
        )

    def refresh_runtime(self):
        lines = [
            f"plugins      : {len(self.pm.plugins)}",
            f"events       : {len(self.pm.event_log)}",
            f"errors       : {len(self.pm.errors)}",
            f"hooks        : {len(self.available_hooks())}",
            f"context_keys : {len(self.pm.context)}",
        ]

        self.runtime.setPlainText(
            "\n".join(lines)
        )

    # =========================================================
    # MOCK
    # =========================================================

    def mock_args(self, hook):
        path = Path("mock/example.lua")

        file_data = {
            "path": path,
            "active": True,
        }

        bundle = {
            "name": "Mock Bundle",
            "files": [file_data],
            "active": True,
        }

        table = {
            "on_app_start":
                [self.mock],

            "before_scan":
                [self.mock, False],

            "after_scan":
                [self.mock, False, {}],

            "detect_category":
                [self.mock, path],

            "format_status":
                [self.mock, "mock"],

            "bundle_color":
                [self.mock, bundle],

            "file_color":
                [self.mock, file_data],

            "format_bundle_row":
                [self.mock, bundle, "mock row"],

            "format_file_row":
                [self.mock, file_data, "mock file"],

            "get_bundle_info":
                [self.mock, bundle],

            "normalize_file_path":
                [self.mock, path, False],

            "should_include_file":
                [self.mock, path, path],

            "on_bundle_selected":
                [self.mock, bundle],

            "on_file_double_click":
                [self.mock, file_data],

            "ui_render":
                [self.mock, self, "toolbar", {}],
        }

        return table.get(
            hook,
            [self.mock],
        )

    # =========================================================
    # RUN
    # =========================================================

    def run_pipeline(self):
        name = self.pipeline_combo.currentText()

        if not name:
            return

        self.pm.run_bootstrap_pipeline(
            name,
            {
                "stage": "debug",
                "reports": [],
            },
        )

        self.refresh_logs()
        self.refresh_runtime()

        self.status.setText(
            f"pipeline {name} executed"
        )

    def run_hook(self):
        hook = self.hook_combo.currentText()

        if hook.startswith(
            "bootstrap_pipeline::"
        ):

            self.run_pipeline()
            return

        if hook == "extension_point":

            self.pm.hook_extension(
                self.mock,
                self.area_combo.currentText(),
                self.phase_combo.currentText(),
            )

        else:
            args = self.mock_args(hook)

            if hook in FIRST_RESULT_HOOKS:

                self.pm.first_result(
                    hook,
                    *args,
                )

            else:

                self.pm.hook(
                    hook,
                    *args,
                )

        self.refresh_logs()
        self.refresh_runtime()

        self.status.setText(
            f"executed {hook}"
        )


def main():
    QApplication.setAttribute(
        Qt.AA_EnableHighDpiScaling
    )

    QApplication.setAttribute(
        Qt.AA_UseHighDpiPixmaps
    )

    app = QApplication(sys.argv)

    window = FastBug()

    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()