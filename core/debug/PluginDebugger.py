from pathlib import Path
from pprint import pformat
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QBrush
from PyQt5.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.PluginManager import PluginBase, PluginManager


class MockAppManager:
    def __init__(self, plugin_manager):
        self.plugin_manager = plugin_manager
        self.context = plugin_manager.context
        self.paths = [Path("mock/GTA V")]
        self.categories = {"BaseGame": [], "Scripts": []}
        self.known_files = set()
        self.detected_files = []

    def hash_file(self, path):
        return f"mock-{path.name}"
    def aliases(self):
        return self.plugin_manager.aliases()


class PluginDebuggerWindow(QMainWindow):
    def __init__(self, plugin_folder="plugins", parent=None):
        super().__init__(parent)
        self.plugin_folder = plugin_folder
        self.plugin_manager = None
        self.mock_app = None
        self.plugins_by_row = []

        self.setWindowTitle("Plugin Debugger")
        self.resize(1120, 760)
        self.setMinimumSize(920, 620)

        self.build_ui()
        self.apply_theme()
        self.reload_plugins()

    def build_ui(self):
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        title = QLabel("Plugin Debugger")
        title.setObjectName("Title")

        self.hook_combo = QComboBox()
        self.hook_combo.setMinimumWidth(220)
        self.hook_combo.addItems(self.available_hooks())

        reload_button = QPushButton("Reload Plugins")
        reload_button.clicked.connect(self.reload_plugins)

        run_button = QPushButton("Run Mock Hook")
        run_button.clicked.connect(self.run_mock_hook)

        clear_button = QPushButton("Clear Log")
        clear_button.clicked.connect(self.clear_event_log)

        toolbar.addWidget(title)
        toolbar.addStretch(1)
        toolbar.addWidget(QLabel("Hook"))
        toolbar.addWidget(self.hook_combo)
        toolbar.addWidget(run_button)
        toolbar.addWidget(reload_button)
        toolbar.addWidget(clear_button)
        layout.addLayout(toolbar)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        left_layout.addWidget(QLabel("Plugins"))
        self.plugin_list = QListWidget()
        self.plugin_list.currentRowChanged.connect(self.refresh_plugin_detail)
        left_layout.addWidget(self.plugin_list, 1)

        left_layout.addWidget(QLabel("Selected Plugin"))
        self.plugin_tabs = QTabWidget()

        self.plugin_overview = QTextEdit()
        self.plugin_overview.setObjectName("Inspector")
        self.plugin_overview.setReadOnly(True)

        self.plugin_data = QTextEdit()
        self.plugin_data.setObjectName("Inspector")
        self.plugin_data.setReadOnly(True)

        self.plugin_hooks_view = QListWidget()
        self.plugin_hooks_view.setObjectName("HookList")

        self.plugin_tabs.addTab(self.plugin_overview, "Overview")
        self.plugin_tabs.addTab(self.plugin_data, "Data")
        self.plugin_tabs.addTab(self.plugin_hooks_view, "Hooks")
        left_layout.addWidget(self.plugin_tabs, 2)

        self.tabs = QTabWidget()

        self.hook_table = QTableWidget(0, 4)
        self.hook_table.setHorizontalHeaderLabels(["Hook", "Plugin", "Callback", "Layer"])
        self.hook_table.horizontalHeader().setStretchLastSection(True)
        self.tabs.addTab(self.hook_table, "Hooks")

        self.event_log = QTextEdit()
        self.event_log.setObjectName("Log")
        self.event_log.setReadOnly(True)
        self.event_log.setLineWrapMode(QTextEdit.NoWrap)
        self.tabs.addTab(self.event_log, "Live Events")

        self.error_log = QTextEdit()
        self.error_log.setObjectName("Log")
        self.error_log.setReadOnly(True)
        self.error_log.setLineWrapMode(QTextEdit.NoWrap)
        self.tabs.addTab(self.error_log, "Errors")

        self.context_view = QTextEdit()
        self.context_view.setObjectName("Log")
        self.context_view.setReadOnly(True)
        self.context_view.setLineWrapMode(QTextEdit.NoWrap)
        self.tabs.addTab(self.context_view, "Context")

        splitter.addWidget(left)
        splitter.addWidget(self.tabs)
        splitter.setSizes([340, 780])

        layout.addWidget(splitter, 1)
        self.setCentralWidget(root)

    def apply_theme(self):
        self.setStyleSheet(
            """
            QWidget {
                background: #000000;
                color: #f2f2f2;
                font-family: Segoe UI, Arial, sans-serif;
                font-size: 12px;
            }

            QLabel#Title {
                font-size: 21px;
                font-weight: 800;
            }

            QListWidget,
            QTableWidget,
            QTextEdit,
            QComboBox {
                background: #090909;
                border: 1px solid #252525;
                border-radius: 6px;
                color: #ffffff;
                selection-background-color: #ffffff;
                selection-color: #000000;
            }

            QTextEdit#Log,
            QTextEdit#Inspector {
                font-family: Consolas, Cascadia Mono, monospace;
                font-size: 12px;
            }

            QListWidget::item {
                padding: 8px;
                border-radius: 5px;
            }

            QListWidget#HookList::item {
                padding: 5px 8px;
            }

            QListWidget::item:selected {
                background: #ffffff;
                color: #000000;
            }

            QTabWidget::pane {
                border: 1px solid #252525;
                border-radius: 6px;
            }

            QTabBar::tab {
                background: #111111;
                color: #dcdcdc;
                border: 1px solid #252525;
                padding: 8px 14px;
                margin-right: 3px;
            }

            QTabBar::tab:selected {
                background: #ffffff;
                color: #000000;
            }

            QHeaderView::section {
                background: #151515;
                color: #ffffff;
                border: 1px solid #252525;
                padding: 5px;
            }

            QPushButton {
                background: #ffffff;
                border: 1px solid #ffffff;
                border-radius: 6px;
                color: #000000;
                font-weight: 700;
                min-height: 30px;
                padding: 6px 12px;
            }
            """
        )

    def available_hooks(self):
        names = set()

        for name in dir(PluginBase):
            if name.startswith("_"):
                continue

            value = getattr(PluginBase, name)

            if callable(value):
                names.add(self.base_hook_name(name))

        return sorted(names)

    def base_hook_name(self, name):
        for suffix in ("_hook", "_process", "_core", "_internal"):
            if name.endswith(suffix):
                return name[: -len(suffix)]

        return name

    def reload_plugins(self):
        self.plugin_manager = PluginManager(self.plugin_folder)
        self.mock_app = MockAppManager(self.plugin_manager)
        self.plugin_manager.hook("on_app_start", self.mock_app)
        self.refresh_all()

    def refresh_all(self):
        self.refresh_plugin_table()
        self.refresh_hook_table()
        self.refresh_event_log()
        self.refresh_error_log()
        self.refresh_context_view()

    def refresh_plugin_table(self):
        plugins = self.plugin_manager.plugins
        selected_row = max(0, self.plugin_list.currentRow())
        self.plugins_by_row = plugins
        self.plugin_list.blockSignals(True)
        self.plugin_list.clear()

        for plugin in plugins:
            name = getattr(plugin, "name", plugin.__class__.__name__)
            version = getattr(plugin, "version", "")
            priority = getattr(plugin, "priority", 100)
            item = QListWidgetItem(f"{name}\nv{version}  |  priority {priority}")
            self.plugin_list.addItem(item)

        if plugins:
            self.plugin_list.setCurrentRow(min(selected_row, len(plugins) - 1))

        self.plugin_list.blockSignals(False)
        self.refresh_plugin_detail()

    def refresh_plugin_detail(self):
        row = self.plugin_list.currentRow()

        if row < 0 or row >= len(self.plugins_by_row):
            self.plugin_overview.setPlainText("No plugin selected.")
            self.plugin_data.setPlainText("")
            self.plugin_hooks_view.clear()
            return

        plugin = self.plugins_by_row[row]
        overview = [
            f"Name: {getattr(plugin, 'name', plugin.__class__.__name__)}",
            f"Version: {getattr(plugin, 'version', '')}",
            f"Description: {getattr(plugin, 'description', '')}",
             f"Author: {getattr(plugin, 'author', '')}",
            f"Priority: {getattr(plugin, 'priority', 100)}",
            f"Class: {plugin.__class__.__name__}",
            f"File: {getattr(plugin, '__plugin_file__', 'built-in')}",
            f"Bootstrap: {getattr(plugin, '__plugin_bootstrap__', False)}",
            "",
        ]

        data = [
            "Extensions",
            self.format_lines(getattr(plugin, "supported_extensions", set()) or set()),
            "",
            "Categories",
            self.format_lines(getattr(plugin, "categories", []) or []),
            "",
            "Ignored Stems",
            self.format_lines(getattr(plugin, "ignored_stems", set()) or set()),
            "",
            "Ignored Parents",
            self.format_lines(getattr(plugin, "ignored_parent_names", set()) or set()),
            "",
            "Aliases",
            self.format_mapping(getattr(plugin, "aliases", {}) or {}),
        ]

        html = """
        <div style="
            font-family: Consolas;
            font-size: 12px;
            color: white;
        ">
        """

        colors = {
            "Name": "#80c7ff",
            "Version": "#9dffb0",
            "Description": "#ffd56f",
            "Author": "#00ff77",
            "Priority": "#ff9f80",
            "Class": "#ff7fff",
            "File": "#c6a7ff",
            "Bootstrap": "#909090",
        }

        for line in overview:
            if ":" not in line:
                html += "<br>"
                continue

            key, value = line.split(":", 1)

            label_html = (
                f'<span style="color:{colors.get(key, "#ffffff")}; '
                f'font-weight:700">{key}:</span>'
            )

            value_html = f'<span style="color:white">{value}</span>'

            if key == "Priority":
                try:
                    priority_value = int(value.strip())

                    if priority_value <= -1:
                        value_html = f"""
                        <span
                            style="
                                color:#ff5c5c;
                                text-decoration: underline;
                                font-weight:700;
                            "
                            title="
        Do not modify this priority unless you understand the plugin load order system.
        Negative priorities are reserved for critical runtime plugins.
                            "
                        >
                            {priority_value}
                        </span>
                        """

                except Exception:
                    pass

            html += f"{label_html}{value_html}<br>"

        html += "</div>"

        self.plugin_overview.setHtml(html)
        self.plugin_data.setPlainText("\n".join(data))
        self.refresh_plugin_hooks(plugin)

    def format_lines(self, values):
        values = sorted(values)

        if not values:
            return "  none"

        return "\n".join(f"  - {value}" for value in values)

    def format_mapping(self, values):
        if not values:
            return "  none"

        return "\n".join(f"  - {key}: {value}" for key, value in sorted(values.items()))

    def refresh_plugin_hooks(self, plugin):
        self.plugin_hooks_view.clear()

        for hook in self.plugin_hooks(plugin):
            item = QListWidgetItem(hook)
            layer = self.hook_layer(hook)

            if layer == "hook":
                item.setForeground(QBrush(QColor("#80c7ff")))
            elif layer == "process":
                item.setForeground(QBrush(QColor("#9dffb0")))
            elif layer == "core":
                item.setForeground(QBrush(QColor("#ffd56f")))
            elif layer == "internal":
                item.setForeground(QBrush(QColor("#ff9f80")))

            self.plugin_hooks_view.addItem(item)

    def plugin_hooks(self, plugin):
        hooks = []

        plugin_class = plugin.__class__

        for hook_name in self.available_hooks():
            for callback_name in self.plugin_manager.callback_names(hook_name):
                #
                # Only count hooks actually implemented
                # by the plugin class itself.
                #

                if callback_name not in plugin_class.__dict__:
                    continue

                callback = getattr(
                    plugin,
                    callback_name,
                    None,
                )

                if callable(callback):
                    hooks.append(callback_name)

        return hooks or ["none"]

    def refresh_hook_table(self):
        rows = []

        for hook_name in self.available_hooks():
            for callback_name in self.plugin_manager.callback_names(hook_name):
                for plugin in self.plugin_manager.plugins:
                    callback = getattr(plugin, callback_name, None)

                    if callable(callback):
                        rows.append(
                            [
                                hook_name,
                                getattr(plugin, "name", plugin.__class__.__name__),
                                callback_name,
                                self.hook_layer(callback_name),
                            ]
                        )

        self.hook_table.setRowCount(len(rows))

        for row, values in enumerate(rows):
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                self.apply_hook_table_color(item, values[3])
                self.hook_table.setItem(row, column, item)

        self.hook_table.resizeColumnsToContents()

    def hook_layer(self, callback_name):
        for suffix in ("_hook", "_process", "_core", "_internal"):
            if callback_name.endswith(suffix):
                return suffix[1:]

        return "base"

    def apply_hook_table_color(self, item, layer):
        colors = {
            "base": "#ffffff",
            "hook": "#80c7ff",
            "process": "#9dffb0",
            "core": "#ffd56f",
            "internal": "#ff9f80",
        }
        item.setForeground(QBrush(QColor(colors.get(layer, "#ffffff"))))

    def refresh_event_log(self):
        lines = []

        for event in self.plugin_manager.event_log:
            data = event.get("data") or {}
            detail = ", ".join(f"{key}={value}" for key, value in data.items())
            suffix = f" | {detail}" if detail else ""
            code = event["code"]
            color = self.event_color(code)
            lines.append(
                f'<span style="color:#707070">{event["index"]:04d}</span> '
                f'<span style="color:{color}; font-weight:700">[{code}]</span> '
                f'<span style="color:#ffffff">{self.escape_html(str(event["message"]))}</span>'
                f'<span style="color:#a9a9a9">{self.escape_html(suffix)}</span>'
            )

        self.event_log.setHtml("<br>".join(lines))
        self.event_log.moveCursor(self.event_log.textCursor().End)

    def refresh_error_log(self):
        if not self.plugin_manager.errors:
            self.error_log.setHtml('<span style="color:#9dffb0">No plugin errors.</span>')
            return

        lines = []

        for index, error in enumerate(self.plugin_manager.errors, start=1):
            lines.append(f'<span style="color:#ff5c5c; font-weight:700">ERROR {index}</span>')
            lines.append(f'<span style="color:#ffd56f">Plugin:</span> {self.escape_html(error.get("plugin", ""))}')
            lines.append(f'<span style="color:#ffd56f">Hook:</span> {self.escape_html(error.get("hook", ""))}')
            lines.append(f'<span style="color:#ffd56f">Message:</span> {self.escape_html(error.get("error", ""))}')
            lines.append(f'<pre style="color:#ff9f80">{self.escape_html(error.get("traceback", ""))}</pre>')

        self.error_log.setHtml("<br>".join(lines))

    def event_color(self, code):
        if "ERROR" in code:
            return "#ff5c5c"

        if "BOOTSTRAP" in code:
            return "#80c7ff"

        if "PLUGIN" in code:
            return "#ffd56f"

        if "CALL_RESULT" in code or "FIRST_RESULT_FOUND" in code:
            return "#9dffb0"

        if "CALL" in code or "HOOK" in code:
            return "#c6a7ff"

        return "#ffffff"

    def escape_html(self, value):
        return (
            value.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    def refresh_context_view(self):
        if not self.plugin_manager.context:
            self.context_view.setHtml(
                '<span style="color:#777">No context values.</span>'
            )
            return

        html = [
            """
            <div style="
                font-family:Consolas;
                font-size:12px;
                color:white;
            ">
            """
        ]

        colors = {
            "dict": "#8be9fd",
            "list": "#ffb86c",
            "key": "#50fa7b",
            "value": "#f8f8f2",
        }

        for key, value in sorted(self.plugin_manager.context.items()):
            if isinstance(value, dict):
                color = colors["dict"]
            elif isinstance(value, list):
                color = colors["list"]
            else:
                color = colors["value"]

            formatted = self.escape_html(
                pformat(value, width=90)
            )

            html.append(
                f"""
                <div style="margin-bottom:10px;">
                    <span style="
                        color:{colors['key']};
                        font-weight:bold;
                    ">
                        {self.escape_html(str(key))}
                    </span>

                    <pre style="
                        margin:4px 0 0 12px;
                        color:{color};
                    ">
    {formatted}
                    </pre>
                </div>
                """
            )

        html.append("</div>")

        self.context_view.setHtml("".join(html))

    def clear_event_log(self):
        self.plugin_manager.event_log.clear()
        self.refresh_event_log()

    def run_mock_hook(self):
        hook_name = self.hook_combo.currentText()
        args = self.mock_args(hook_name)

        self.plugin_manager.log_event(
            "MOCK_HOOK",
            hook_name,
            hook=hook_name,
            args=", ".join(type(arg).__name__ for arg in args),
        )

        if hook_name in self.result_hooks():
            self.plugin_manager.first_result(hook_name, *args)
        else:
            self.plugin_manager.hook(hook_name, *args)

        self.refresh_all()

    def result_hooks(self):
        return {
            "normalize_file_path",
            "should_include_file",
            "detect_category",
            "clean_bundle_name",
            "get_bundle_name",
            "format_bundle_row",
            "format_file_row",
            "format_status",
        }

    def mock_args(self, hook_name):
        path = Path("mock/GTA V/scripts/example.lua")
        actual_path = path
        file_data = {"path": path, "active": True}
        bundle = {"name": "Mock Bundle", "files": [file_data], "active": True}

        args_by_hook = {
            "plugin_manager_bootstrap": [self.plugin_manager],
            "before_plugins_loaded": [self.plugin_manager],
            "after_plugins_loaded": [self.plugin_manager],
            "before_plugin_loaded": [self.plugin_manager, Path("plugins/mock.py")],
            "after_plugin_loaded": [self.plugin_manager, self.plugin_manager.plugins[-1]],
            "on_plugin_registered": [self.plugin_manager, self.plugin_manager.plugins[-1]],
            "on_plugin_error": [self.plugin_manager, {"plugin": "mock", "error": "Mock error"}],
            "on_app_start": [self.mock_app],
            "on_config_loaded": [self.mock_app, {}],
            "on_config_saving": [self.mock_app, {}],
            "on_folder_added": [self.mock_app, Path("mock/GTA V")],
            "on_folder_removed": [self.mock_app, Path("mock/GTA V")],
            "before_scan": [self.mock_app, False],
            "after_scan": [self.mock_app, False, {}],
            "normalize_file_path": [self.mock_app, path, False],
            "should_include_file": [self.mock_app, path, actual_path],
            "detect_category": [self.mock_app, path],
            "clean_bundle_name": [self.mock_app, "ExamplePlugin"],
            "get_bundle_name": [self.mock_app, path, actual_path, "Scripts"],
            "on_new_file_detected": [self.mock_app, path],
            "on_file_grouped": [self.mock_app, path, "Scripts", "Mock Bundle", file_data],
            "after_bundle_built": [self.mock_app, "Scripts", bundle],
            "before_toggle_bundle": [self.mock_app, bundle, False],
            "before_toggle_file": [self.mock_app, path, False],
            "after_toggle_file": [self.mock_app, path, path.with_name("example.lua.disabled"), False],
            "after_toggle_bundle": [self.mock_app, bundle, False],
            "before_disable_file": [self.mock_app, path],
            "after_disable_file": [self.mock_app, path, path.with_name("example.lua.disabled")],
            "on_ui_ready": [self.mock_app, self],
            "on_ui_refreshed": [self.mock_app, self],
            "on_bundle_selected": [self.mock_app, bundle],
            "on_bundle_double_click": [self.mock_app, bundle],
            "on_file_double_click": [self.mock_app, file_data],
            "format_bundle_row": [self.mock_app, bundle, "Mock row"],
            "format_file_row": [self.mock_app, file_data, "Mock file row"],
            "format_status": [self.mock_app, "Mock status"],
        }

        return args_by_hook.get(hook_name, [self.mock_app])


def main():
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = PluginDebuggerWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
