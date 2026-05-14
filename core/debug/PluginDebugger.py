import json
from copy import deepcopy
from pathlib import Path
from pprint import pformat
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QBrush, QGuiApplication
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QAbstractItemView,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
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
    QToolBar,
    QVBoxLayout,
    QWidget,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEBUG_DIR = Path(__file__).resolve().parent
DEBUG_CONFIG_PATH = DEBUG_DIR / "config.json"

DEFAULT_DEBUG_UI_CONFIG = {
    "scale": 0.78,
    "dpi_cap": 1.25,
    "use_dpi": True,
    "window": {
        "width_ratio": 0.82,
        "height_ratio": 0.78,
        "min_width": 820,
        "min_height": 500,
        "width_cap": 1480,
        "height_cap": 960,
    },
    "layout": {
        "root_margins": [3, 2, 3, 3],
        "root_spacing": 3,
        "detail_left_margin": 5,
        "status_margins": [3, 1, 3, 1],
    },
    "splitters": {
        "inner_center_fraction_of_open_w": 0.48,
        "inner_list_of_iw": [0.24, 0.76],
        "mod_center_fraction_of_open_w": 0.54,
        "mod_main_of_mw": [0.67, 0.33],
        "outer_output_ratio_of_open_w": 0.34,
        "outer_gap_px": 8,
        "inner_plugin_col_min": 180,
        "inner_detail_col_min": 300,
        "mod_main_min": 360,
        "mod_coverage_min": 220,
        "outer_output_min": 300,
        "outer_main_min": 480,
    },
}


def _deep_merge_defaults(base, overrides):
    out = deepcopy(base)
    for key, value in (overrides or {}).items():
        if key in out and isinstance(out[key], dict) and isinstance(value, dict):
            _deep_merge_defaults(out[key], value)
        else:
            out[key] = value
    return out


def load_plugin_debugger_config(path=None):
    path = path or DEBUG_CONFIG_PATH
    data = {}
    try:
        if path.is_file():
            data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        pass
    return _deep_merge_defaults(DEFAULT_DEBUG_UI_CONFIG, data)

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.PluginManager import PluginManager
from core.plugin_hook_registry import (
    DECLARED_HOOK_NAMES,
    EXTENSION_AREAS,
    EXTENSION_PHASES,
    FIRST_RESULT_HOOKS,
    discover_bootstrap_pipeline_methods,
)


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
    def __init__(self, plugin_folder="plugins", parent=None, config_path=None):
        super().__init__(parent)
        self.plugin_folder = plugin_folder
        self.plugin_manager = None
        self.mock_app = None
        self.plugins_by_row = []
        self._config = load_plugin_debugger_config(config_path)

        self.setWindowTitle("Plugin Debugger")
        wcfg = self._config.get("window", {})
        min_w = int(wcfg.get("min_width", 820))
        min_h = int(wcfg.get("min_height", 500))
        self.setMinimumSize(min_w, min_h)
        app_inst = QApplication.instance()
        self._open_w = 1100
        self._open_h = 720
        if app_inst is not None:
            desk = app_inst.desktop().availableGeometry()
            wr = float(wcfg.get("width_ratio", 0.70))
            hr = float(wcfg.get("height_ratio", 0.74))
            w_cap = int(wcfg.get("width_cap", 1480))
            h_cap = int(wcfg.get("height_cap", 960))
            w = max(min_w, min(w_cap, int(desk.width() * wr)))
            h = max(min_h, min(h_cap, int(desk.height() * hr)))
            self._open_w, self._open_h = w, h
            self.resize(w, h)

        self.build_ui()
        self.apply_theme()
        self.reload_plugins()

    def build_ui(self):
        self.corner_reload = QPushButton("Reload")
        self.corner_reload.setObjectName("CornerButton")
        self.corner_reload.clicked.connect(self.reload_plugins)

        self.corner_clear = QPushButton("Clear log")
        self.corner_clear.setObjectName("CornerButton")
        self.corner_clear.clicked.connect(self.clear_event_log)

        root = QWidget()
        root.setObjectName("AppRoot")
        layout = QVBoxLayout(root)
        lcm = self._config.get("layout", {}).get("root_margins", [3, 2, 3, 3])
        layout.setContentsMargins(int(lcm[0]), int(lcm[1]), int(lcm[2]), int(lcm[3]))
        layout.setSpacing(int(self._config.get("layout", {}).get("root_spacing", 3)))

        head = QHBoxLayout()
        ta = QVBoxLayout()
        ta.setSpacing(0)
        t = QLabel("PLUGIN DEBUGGER")
        t.setObjectName("Title")
        st = QLabel("mock hooks · events · registry")
        st.setObjectName("Subtitle")
        ta.addWidget(t)
        ta.addWidget(st)
        head.addLayout(ta, 1)
        layout.addLayout(head)

        tb = QToolBar()
        tb.setMovable(False)
        tb.setFloatable(False)
        self.addToolBar(tb)

        self.hook_combo = QComboBox()
        sc = self._ui_scale()
        self.hook_combo.setMinimumWidth(max(160, int(160 * sc)))
        self.hook_combo.addItems(self.available_hooks())
        self.hook_combo.currentTextChanged.connect(self._on_hook_combo_changed)

        self.extension_area_combo = QComboBox()
        self.extension_area_combo.addItems(list(EXTENSION_AREAS))
        self.extension_phase_combo = QComboBox()
        self.extension_phase_combo.addItems(list(EXTENSION_PHASES))

        self.pipeline_combo = QComboBox()
        self.pipeline_combo.setMinimumWidth(max(100, int(110 * sc)))

        run_btn = QPushButton("Run mock")
        run_btn.setObjectName("SecondaryButton")
        run_btn.clicked.connect(self.run_mock_hook)
        pipe_btn = QPushButton("Run pipeline")
        pipe_btn.setObjectName("SecondaryButton")
        pipe_btn.clicked.connect(self.run_bootstrap_pipeline_mock)

        tb.addWidget(QLabel("Hook"))
        tb.addWidget(self.hook_combo)
        tb.addWidget(QLabel("ext"))
        tb.addWidget(self.extension_area_combo)
        tb.addWidget(self.extension_phase_combo)
        tb.addWidget(QLabel("pipe"))
        tb.addWidget(self.pipeline_combo)
        tb.addSeparator()
        tb.addWidget(run_btn)
        tb.addWidget(pipe_btn)

        outer = QSplitter(Qt.Horizontal)
        outer.setChildrenCollapsible(False)

        mod_split = QSplitter(Qt.Horizontal)
        mod_split.setChildrenCollapsible(False)

        center = QWidget()
        cl = QVBoxLayout(center)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(4)

        inner = QSplitter(Qt.Horizontal)
        inner.setChildrenCollapsible(False)

        list_wrap = QWidget()
        ll = QVBoxLayout(list_wrap)
        ll.setContentsMargins(0, 0, 0, 0)
        ll.setSpacing(4)
        ll.addWidget(QLabel("Plugins"))
        self.plugin_list = QListWidget()
        self.plugin_list.setObjectName("FolderList")
        self.plugin_list.currentRowChanged.connect(self.refresh_plugin_detail)
        ll.addWidget(self.plugin_list, 1)

        detail_wrap = QWidget()
        detail_wrap.setObjectName("DetailsPane")
        dl = QVBoxLayout(detail_wrap)
        dlm = int(self._config.get("layout", {}).get("detail_left_margin", 5))
        dl.setContentsMargins(dlm, 0, 0, 0)
        dl.setSpacing(4)
        dl.addWidget(QLabel("Detail"))
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
        dl.addWidget(self.plugin_tabs, 1)

        inner.addWidget(list_wrap)
        inner.addWidget(detail_wrap)
        sp = self._config.get("splitters", {})
        iw_frac = float(sp.get("inner_center_fraction_of_open_w", 0.48))
        iw = max(520, int(self._open_w * iw_frac))
        ir = sp.get("inner_list_of_iw", [0.24, 0.76])
        ip_min = int(sp.get("inner_plugin_col_min", 180))
        id_min = int(sp.get("inner_detail_col_min", 300))
        inner.setSizes(
            [
                max(ip_min, int(iw * float(ir[0]))),
                max(id_min, int(iw * float(ir[1]))),
            ]
        )
        inner.setStretchFactor(0, 0)
        inner.setStretchFactor(1, 1)

        cl.addWidget(inner, 1)

        ext = QWidget()
        ext.setObjectName("PluginSidebar")
        esl = QVBoxLayout(ext)
        esl.setContentsMargins(0, 0, 0, 0)
        esl.setSpacing(4)
        sh = QLabel("Coverage")
        sh.setObjectName("SectionLabel")
        esl.addWidget(sh)
        self.hook_table = QTableWidget(0, 4)
        self.hook_table.setHorizontalHeaderLabels(["Hook", "Plugin", "Callback", "Layer"])
        self.hook_table.setWordWrap(True)
        self.hook_table.setTextElideMode(Qt.ElideNone)
        self.hook_table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.hook_table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        hh = self.hook_table.horizontalHeader()
        hh.setStretchLastSection(False)
        hh.setMinimumSectionSize(72)
        hh.setSectionResizeMode(0, QHeaderView.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.hook_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        esl.addWidget(self.hook_table, 1)

        mod_split.addWidget(center)
        mod_split.addWidget(ext)
        mw_frac = float(sp.get("mod_center_fraction_of_open_w", 0.54))
        mw = max(560, int(self._open_w * mw_frac))
        mr = sp.get("mod_main_of_mw", [0.67, 0.33])
        mm_min = int(sp.get("mod_main_min", 360))
        mc_min = int(sp.get("mod_coverage_min", 220))
        mod_split.setSizes(
            [
                max(mm_min, int(mw * float(mr[0]))),
                max(mc_min, int(mw * float(mr[1]))),
            ]
        )
        mod_split.setStretchFactor(0, 2)
        mod_split.setStretchFactor(1, 1)

        side = QWidget()
        sl = QVBoxLayout(side)
        sl.setContentsMargins(0, 0, 0, 0)
        sl.setSpacing(4)
        out_box = QGroupBox("Output")
        ol = QVBoxLayout(out_box)
        self.tabs = QTabWidget()
        self.event_log = QTextEdit()
        self.event_log.setObjectName("Log")
        self.event_log.setReadOnly(True)
        self.event_log.setLineWrapMode(QTextEdit.WidgetWidth)
        self.error_log = QTextEdit()
        self.error_log.setObjectName("Log")
        self.error_log.setReadOnly(True)
        self.error_log.setLineWrapMode(QTextEdit.WidgetWidth)
        self.context_view = QTextEdit()
        self.context_view.setObjectName("Log")
        self.context_view.setReadOnly(True)
        self.context_view.setLineWrapMode(QTextEdit.WidgetWidth)
        self.debug_props = QTextEdit()
        self.debug_props.setObjectName("Log")
        self.debug_props.setReadOnly(True)
        self.debug_props.setLineWrapMode(QTextEdit.WidgetWidth)
        self.tabs.addTab(self.event_log, "Events")
        self.tabs.addTab(self.error_log, "Errors")
        self.tabs.addTab(self.context_view, "Context")
        self.tabs.addTab(self.debug_props, "Runtime")
        ol.addWidget(self.tabs)
        sl.addWidget(out_box, 1)

        outer.addWidget(mod_split)
        outer.addWidget(side)
        ow = self._open_w
        out_ratio = float(sp.get("outer_output_ratio_of_open_w", 0.36))
        gap = int(sp.get("outer_gap_px", 8))
        out_w = max(int(sp.get("outer_output_min", 300)), int(ow * out_ratio))
        main_w = max(int(sp.get("outer_main_min", 480)), ow - out_w - gap)
        outer.setSizes([main_w, out_w])
        outer.setStretchFactor(0, 3)
        outer.setStretchFactor(1, 2)

        layout.addWidget(outer, 1)

        status_row = QWidget()
        status_row.setObjectName("StatusStrip")
        srl = QHBoxLayout(status_row)
        sm = self._config.get("layout", {}).get("status_margins", [3, 1, 3, 1])
        srl.setContentsMargins(int(sm[0]), int(sm[1]), int(sm[2]), int(sm[3]))
        self.debug_status_label = QLabel()
        self.debug_status_label.setObjectName("Status")
        srl.addWidget(self.debug_status_label, 1)
        layout.addWidget(status_row)

        self.setCentralWidget(root)
        self._build_debug_menubar()
        self._on_hook_combo_changed(self.hook_combo.currentText())
        self._refresh_pipeline_combo()

    def _build_debug_menubar(self):
        bar = self.menuBar()
        bar.setCornerWidget(self.corner_reload, Qt.TopLeftCorner)
        bar.setCornerWidget(self.corner_clear, Qt.TopRightCorner)
        exit_act = QAction("Exit", self)
        exit_act.triggered.connect(self.close)
        bar.addMenu("File").addAction(exit_act)

    def _ui_scale(self):
        cfg = self._config
        user = float(cfg.get("scale", 0.78))
        cap = float(cfg.get("dpi_cap", 1.25))
        if cfg.get("use_dpi", True):
            screen = QGuiApplication.primaryScreen()
            dpi = screen.logicalDotsPerInchX() / 96.0 if screen else 1.0
            base = min(dpi, cap)
        else:
            base = 1.0
        s = base * user
        return max(0.5, min(2.0, s))

    def apply_theme(self):
        s = self._ui_scale()
        px = lambda n: max(10, int(round(n * s)))
        self._html_body_px = px(13)
        self._ctx_pre_width = max(40, int(72 * s))
        hb = px(13)
        title_px = px(16)
        sub_px = px(12)
        sec_px = px(11)
        stat_px = px(12)
        corner_fs = px(12)
        tab_pad_v, tab_pad_h = px(6), px(12)
        hdr_pad = px(5)
        dd_w = px(22)
        self.setStyleSheet(
            """
            QWidget#AppRoot {{
                background-color: #000000;
            }}
            QWidget {{
                background-color: transparent;
                color: #d0d0d0;
                font-family: "Cascadia Mono", "Consolas", "JetBrains Mono", monospace;
                font-size: {hb}px;
            }}
            QMainWindow {{
                background-color: #000000;
            }}
            QMenuBar {{
                background-color: #000000;
                color: #b0b0b0;
                border-bottom: 1px solid #1a1a1a;
                padding: 0;
                spacing: 0;
            }}
            QMenuBar::item {{
                padding: {mip_v}px {mip_h}px;
                border-radius: 0;
            }}
            QMenuBar::item:selected {{
                background-color: #111111;
                color: #ffffff;
            }}
            QMenu {{
                background-color: #000000;
                border: 1px solid #333333;
                border-radius: 0;
                padding: 0;
            }}
            QMenu::item {{
                padding: {mitem_v}px {mitem_h}px;
            }}
            QMenu::item:selected {{
                background-color: #1a1a1a;
                color: #ffffff;
            }}
            QPushButton#CornerButton {{
                background-color: #000000;
                color: #d0d0d0;
                border: 1px solid #333333;
                border-radius: 0;
                padding: {cb_pad_v}px {cb_pad_h}px;
                font-weight: 700;
                font-size: {corner_fs}px;
                min-height: {cb_min}px;
                max-height: {cb_max}px;
            }}
            QPushButton#CornerButton:hover {{
                background-color: #111111;
                color: #ffffff;
            }}
            QToolBar {{
                background-color: #000000;
                border: none;
                border-bottom: 1px solid #1a1a1a;
                spacing: {tb_sp}px;
                padding: {tb_pv}px {tb_ph}px;
                min-height: {tb_mh}px;
            }}
            QLabel#Title {{
                color: #ffffff;
                font-size: {title_px}px;
                font-weight: 700;
            }}
            QLabel#Subtitle,
            QLabel#PanelHint {{
                color: #707070;
                font-size: {sub_px}px;
            }}
            QLabel#SectionLabel {{
                color: #909090;
                font-size: {sec_px}px;
                font-weight: 700;
                letter-spacing: 1px;
            }}
            QWidget#StatusStrip {{
                background-color: #000000;
                border: none;
                border-top: 1px solid #1a1a1a;
            }}
            QLabel#Status {{
                color: #707070;
                padding: {st_pv}px 0;
                font-size: {stat_px}px;
            }}
            QGroupBox {{
                border: 1px solid #222222;
                border-radius: 0;
                margin-top: {gb_mt}px;
                padding: {gb_pt}px {gb_pr}px {gb_pb}px {gb_pl}px;
                background-color: #000000;
                font-weight: 700;
                color: #c0c0c0;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: {gb_tl}px;
                padding: 0 {gb_tpad}px;
                color: #ffffff;
            }}
            QLineEdit,
            QListWidget,
            QComboBox,
            QTextEdit,
            QTableWidget {{
                background-color: #000000;
                border: 1px solid #333333;
                border-radius: 0;
                color: #e8e8e8;
                padding: {inp_pv}px {inp_ph}px;
                selection-background-color: #303030;
                selection-color: #ffffff;
            }}
            QTextEdit#Log,
            QTextEdit#Inspector {{
                padding: {log_pad}px;
            }}
            QListWidget::item {{
                padding: {lw_iv}px {lw_ih}px;
                border-radius: 0;
            }}
            QListWidget::item:hover {{
                background-color: #0d0d0d;
            }}
            QListWidget::item:selected {{
                background-color: #1a1a1a;
                color: #ffffff;
                border: 1px solid #444444;
            }}
            QComboBox::drop-down {{
                border: 0;
                width: {dd_w}px;
            }}
            QComboBox QAbstractItemView {{
                background-color: #000000;
                border: 1px solid #333333;
                color: #e8e8e8;
                selection-background-color: #303030;
                selection-color: #ffffff;
                outline: 0;
                border-radius: 0;
            }}
            QPushButton {{
                background-color: #0a0a0a;
                border: 1px solid #333333;
                border-radius: 0;
                color: #d0d0d0;
                font-weight: 700;
                min-height: {btn_mh}px;
                padding: {btn_pv}px {btn_ph}px;
            }}
            QPushButton#SecondaryButton {{
                background-color: #000000;
                border-color: #333333;
                color: #b0b0b0;
            }}
            QPushButton#SecondaryButton:hover {{
                background-color: #111111;
                border-color: #555555;
                color: #ffffff;
            }}
            QPushButton:hover {{
                background-color: #141414;
                border-color: #555555;
            }}
            QWidget#DetailsPane {{
                border-left: 1px solid #1a1a1a;
            }}
            QWidget#PluginSidebar {{
                border-left: 1px solid #1a1a1a;
                padding-left: {ps_pl}px;
            }}
            QTabWidget::pane {{
                border: 1px solid #222222;
                border-radius: 0;
                top: -1px;
            }}
            QTabBar::tab {{
                background: #000000;
                color: #707070;
                border: 1px solid #333333;
                padding: {tab_pad_v}px {tab_pad_h}px;
                margin-right: 2px;
                border-bottom: none;
                border-top-left-radius: 0;
                border-top-right-radius: 0;
            }}
            QTabBar::tab:selected {{
                background: #111111;
                color: #ffffff;
            }}
            QHeaderView::section {{
                background: #0a0a0a;
                color: #c0c0c0;
                border: 1px solid #333333;
                padding: {hdr_pad}px;
            }}
            QTableWidget {{
                gridline-color: #222222;
            }}
            QSplitter::handle {{
                background-color: #111111;
            }}
            QSplitter::handle:hover {{
                background-color: #333333;
            }}
            QSplitter::handle:horizontal {{
                width: {spl_w}px;
            }}
            QScrollBar:vertical {{
                border: none;
                background: #0a0a0a;
                width: {sb_w}px;
                margin: 0;
            }}
            QScrollBar:horizontal {{
                border: none;
                background: #0a0a0a;
                height: {sb_w}px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: #383838;
                min-height: {sb_min}px;
                border-radius: {sb_r}px;
            }}
            QScrollBar::handle:horizontal {{
                background: #383838;
                min-width: {sb_min}px;
                border-radius: {sb_r}px;
            }}
            QScrollBar::handle:vertical:hover,
            QScrollBar::handle:horizontal:hover {{
                background: #505050;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical,
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {{
                height: 0;
                width: 0;
            }}
            """.format(
                hb=hb,
                mip_v=px(5),
                mip_h=px(10),
                mitem_v=px(6),
                mitem_h=px(20),
                cb_pad_v=px(2),
                cb_pad_h=px(8),
                corner_fs=corner_fs,
                cb_min=px(20),
                cb_max=px(26),
                tb_sp=px(4),
                tb_pv=px(2),
                tb_ph=px(4),
                tb_mh=px(24),
                title_px=title_px,
                sub_px=sub_px,
                sec_px=sec_px,
                st_pv=px(2),
                stat_px=stat_px,
                gb_mt=px(12),
                gb_pt=px(10),
                gb_pr=px(8),
                gb_pb=px(8),
                gb_pl=px(8),
                gb_tl=px(8),
                gb_tpad=px(4),
                inp_pv=px(6),
                inp_ph=px(8),
                log_pad=px(6),
                lw_iv=px(4),
                lw_ih=px(6),
                dd_w=dd_w,
                btn_mh=px(28),
                btn_pv=px(6),
                btn_ph=px(12),
                ps_pl=px(6),
                tab_pad_v=tab_pad_v,
                tab_pad_h=tab_pad_h,
                hdr_pad=hdr_pad,
                spl_w=max(4, px(5)),
                sb_w=max(8, px(10)),
                sb_min=max(28, px(32)),
                sb_r=max(2, px(3)),
            )
        )

    def refresh_debug_properties(self):
        pm = self.plugin_manager
        if getattr(self, "debug_status_label", None) and pm:
            self.debug_status_label.setText(
                f"{len(pm.plugins)} plugins | {len(pm.event_log)} events | {len(pm.errors)} errors"
            )
        if not getattr(self, "debug_props", None) or not pm:
            return

        ctx = pm.context or {}
        q = ctx.get("plugin_review_queue") or []
        perm = ctx.get("permission_pipeline_last") or {}
        lines = [
            f"plugin_folder: {pm.plugin_folder}",
            f"bootstrap_folder: {pm.bootstrap_folder}",
            f"plugins_loaded: {len(pm.plugins)}",
            f"errors: {len(pm.errors)}",
            f"event_log_entries: {len(pm.event_log)}",
            f"loaded_files: {len(pm.loaded_files)}",
            f"declared_hook_names: {len(DECLARED_HOOK_NAMES)}",
            f"extension_grid: {len(EXTENSION_AREAS)} x {len(EXTENSION_PHASES)}",
            f"plugin_review_queue: {len(q)}",
            f"permission_pipeline_last.stage: {perm.get('stage', '')}",
            f"permission_pipeline_last.reports: {len(perm.get('reports', []) or [])}",
        ]

        if pm.event_log:
            last = pm.event_log[-1]
            lines.append(f"last_event: [{last.get('code')}] {last.get('message', '')}")

        self.debug_props.setPlainText("\n".join(lines))

    def available_hooks(self):
        names = list(DECLARED_HOOK_NAMES)
        seen = set(names)
        dynamic = []

        if self.plugin_manager:
            for plugin in self.plugin_manager.plugins:
                for pipeline in discover_bootstrap_pipeline_methods(plugin):
                    token = f"bootstrap_pipeline::{pipeline}"

                    if token not in seen:
                        seen.add(token)
                        dynamic.append(token)

        dynamic.sort()
        return names + dynamic

    def _refresh_pipeline_combo(self):
        self.pipeline_combo.blockSignals(True)
        self.pipeline_combo.clear()
        names = set()

        if self.plugin_manager:
            for plugin in self.plugin_manager.plugins:
                names.update(discover_bootstrap_pipeline_methods(plugin))

        if not names:
            names.add("permission")

        for name in sorted(names):
            self.pipeline_combo.addItem(name)

        self.pipeline_combo.blockSignals(False)

    def _on_hook_combo_changed(self, text):
        is_ext = text == "extension_point"
        self.extension_area_combo.setEnabled(is_ext)
        self.extension_phase_combo.setEnabled(is_ext)

    def base_hook_name(self, name):
        for suffix in ("_hook", "_process", "_core", "_internal"):
            if name.endswith(suffix):
                return name[: -len(suffix)]

        return name

    def reload_plugins(self):
        self.plugin_manager = PluginManager(self.plugin_folder)
        self.mock_app = MockAppManager(self.plugin_manager)
        self.plugin_manager.hook("on_app_start", self.mock_app)
        self.hook_combo.blockSignals(True)
        self.hook_combo.clear()
        self.hook_combo.addItems(self.available_hooks())
        self.hook_combo.blockSignals(False)
        self._refresh_pipeline_combo()
        self._on_hook_combo_changed(self.hook_combo.currentText())
        self.refresh_all()

    def refresh_all(self):
        self.refresh_plugin_table()
        self.refresh_hook_table()
        self.refresh_event_log()
        self.refresh_error_log()
        self.refresh_context_view()
        self.refresh_debug_properties()

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
        report = getattr(plugin, "__plugin_permission_report__", None)

        if report:
            overview.append(f"Permission scan (heuristic): dangerous={report.get('dangerous')}")
            overview.append(f"Permissions: {', '.join(report.get('permissions') or [])}")
            overview.append("")

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

        hp = getattr(self, "_html_body_px", 13)
        html = f"""
        <div style="
            font-family: Consolas;
            font-size: {hp}px;
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

    def _iter_callbacks_for_hook_row(self, hook_name):
        if hook_name.startswith("bootstrap_pipeline::"):
            pipeline = hook_name.split("::", 1)[1]
            return self.plugin_manager.callback_names(f"bootstrap_pipeline_{pipeline}")

        return self.plugin_manager.callback_names(hook_name)

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
            for callback_name in self._iter_callbacks_for_hook_row(hook_name):
                if callback_name not in plugin_class.__dict__:
                    continue

                callback = getattr(plugin, callback_name, None)

                if callable(callback):
                    hooks.append(callback_name)

        return hooks or ["none"]

    def refresh_hook_table(self):
        rows = []

        for hook_name in self.available_hooks():
            for callback_name in self._iter_callbacks_for_hook_row(hook_name):
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

        if len(rows) <= 300:
            self.hook_table.resizeRowsToContents()
        else:
            self.hook_table.verticalHeader().setDefaultSectionSize(24)

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

        for event in self.plugin_manager.event_log[-1000:]:
            data = event.get("data") or {}
            detail = ", ".join(f"{key}={value}" for key, value in data.items())
            suffix = f" | {detail}" if detail else ""
            code = event["code"]
            lines.append(
                f'{event["index"]:04d} [{code}] {event["message"]}{suffix}'
            )

        self.event_log.setPlainText("\n".join(lines))
        self.event_log.moveCursor(self.event_log.textCursor().End)

    def refresh_error_log(self):
        if not self.plugin_manager.errors:
            self.error_log.setPlainText("No plugin errors.")
            return

        lines = []

        for index, error in enumerate(self.plugin_manager.errors, start=1):
            lines.append(f"ERROR {index}")
            lines.append(f'Plugin: {error.get("plugin", "")}')
            lines.append(f'Hook: {error.get("hook", "")}')
            lines.append(f'Message: {error.get("error", "")}')
            lines.append(str(error.get("traceback", "")))

        self.error_log.setPlainText("\n".join(lines))

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

        if "EXTENSION" in code:
            return "#bd93f9"

        return "#ffffff"

    def escape_html(self, value):
        return (
            value.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    def refresh_context_view(self):
        if not self.plugin_manager.context:
            self.context_view.setPlainText("No context values.")
            return

        cw = getattr(self, "_ctx_pre_width", 72)
        lines = []

        for key, value in sorted(self.plugin_manager.context.items()):
            lines.append(str(key))
            lines.append(pformat(value, width=cw))
            lines.append("")

        self.context_view.setPlainText("\n".join(lines))

    def clear_event_log(self):
        self.plugin_manager.event_log.clear()
        self.refresh_event_log()

    def run_bootstrap_pipeline_mock(self):
        name = self.pipeline_combo.currentText()

        if not name:
            return

        self.plugin_manager.log_event(
            "MOCK_BOOTSTRAP_PIPELINE",
            name,
            pipeline=name,
        )
        self.plugin_manager.run_bootstrap_pipeline(
            name, {"stage": "debug", "reports": []}
        )
        self.refresh_all()

    def run_mock_hook(self):
        hook_name = self.hook_combo.currentText()

        if hook_name.startswith("bootstrap_pipeline::"):
            self.run_bootstrap_pipeline_named(hook_name.split("::", 1)[1])
            return

        if hook_name == "extension_point":
            self.plugin_manager.log_event(
                "MOCK_HOOK",
                hook_name,
                hook=hook_name,
                area=self.extension_area_combo.currentText(),
                phase=self.extension_phase_combo.currentText(),
            )
            self.plugin_manager.hook_extension(
                self.mock_app,
                self.extension_area_combo.currentText(),
                self.extension_phase_combo.currentText(),
            )
            self.refresh_all()
            return

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

    def run_bootstrap_pipeline_named(self, name):
        self.plugin_manager.log_event(
            "MOCK_BOOTSTRAP_PIPELINE",
            name,
            pipeline=name,
        )
        self.plugin_manager.run_bootstrap_pipeline(
            name, {"stage": "debug", "reports": []}
        )
        self.refresh_all()

    def result_hooks(self):
        return set(FIRST_RESULT_HOOKS)

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
            "get_bundle_info": [self.mock_app, bundle],
            "bundle_color": [self.mock_app, bundle],
            "file_color": [self.mock_app, file_data],
            "ui_render": [self.mock_app, self, "toolbar", {}],
            "row_render_process": [self.mock_app, bundle, "mock row"],
            "row_render_bundle_process": [self.mock_app, bundle, "mock bundle row"],
            "row_render_file_process": [self.mock_app, file_data, "mock file row"],
            "before_action": [self.mock_app, "mock_action"],
            "after_action": [self.mock_app, "mock_action"],
            "before_ui_action": [self.mock_app, "mock_ui"],
            "after_ui_action": [self.mock_app, "mock_ui"],
            "before_scan_action": [self.mock_app, False],
            "after_scan_action": [self.mock_app, False],
            "before_toggle_action": [self.mock_app, bundle, False],
            "after_toggle_action": [self.mock_app, bundle, False],
        }

        return args_by_hook.get(hook_name, [self.mock_app])


def main():
    from PyQt5.QtCore import Qt as QtCoreQt
    from PyQt5.QtWidgets import QApplication

    QApplication.setAttribute(QtCoreQt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(QtCoreQt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    window = PluginDebuggerWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
