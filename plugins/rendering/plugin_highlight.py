"""
Plugin Highlight
================

Helper-first color system plugin.

This plugin demonstrates:
1) Class-based hooks (bundle_color/file_color/format rows/status).
2) Helper.patch chaining on generated hook names.
3) Context bookkeeping for debugging and future extensions.
"""

from core.PluginManager import Helper, PluginBase


@Helper.patch(PluginBase._bundle_color)
def patch_bundle_color(result, context):
    """
    Final color normalizer for bundle_color results.
    Ensures returned structures are always valid color specs.
    """
    if result is None:
        return None

    if isinstance(result, str):
        return {"fg": result}

    if isinstance(result, (tuple, list)):
        fg = result[0] if len(result) > 0 else None
        bg = result[1] if len(result) > 1 else None
        return {"fg": fg, "bg": bg}

    if isinstance(result, dict):
        return {
            "fg": result.get("fg") or result.get("color"),
            "bg": result.get("bg") or result.get("background"),
        }

    return None


@Helper.patch(PluginBase._file_color)
def patch_file_color(result, context):
    """
    Same normalization logic for file rows.
    """
    return patch_bundle_color(result, context)


@Helper.patch("format_bundle_row")
def patch_bundle_row(result, context):
    """
    If plugins return non-string rows, collapse to safe text.
    """
    if result is None:
        return None

    if isinstance(result, dict):
        return result.get("text")

    if isinstance(result, (tuple, list)) and result:
        return str(result[0])

    return result


class Plugin(PluginBase):
    name = "Plugin Highlight"
    version = "0.0.1"
    description = "Highlights hints and core mods"
    author = "Team Stratware"
    priority = 210

    CORE_MODS = {
        "scripthookv",
        "scripthookvdotnet",
        "ragepluginhook",
        "openiv",
    }

    LOADER_HINTS = (
        "dinput8",
        "scripthook",
        "ragepluginhook",
        "asi loader",
        "openiv",
    )

    PERF_HINTS = (
        "heap",
        "pool",
        "limit",
        "adjuster",
        "optimizer",
        "streamer",
    )

    GRAPHICS_HINTS = (
        "reshade",
        "enb",
        "d3d",
        "dxgi",
        "visual",
        "shader",
        "light",
        "texture",
        "graphic",
    )

    SCRIPT_HINTS = (
        "script",
        "trainer",
        "hook",
        "menu",
        "native",
        "lua",
    )

    def ensure_color_state(self, manager):
        manager.context.setdefault(
            "color_plugin",
            {
                "bundle_groups": {},
                "applied_rows": 0,
            },
        )

    def on_app_start_hook(self, manager):
        self.ensure_color_state(manager)

    def on_ui_ready_hook(self, manager, window):
        self.ensure_color_state(manager)

    def before_scan_hook(self, manager, initial):
        self.ensure_color_state(manager)
        manager.context["color_plugin"]["bundle_groups"] = {}

    def after_bundle_built_hook(self, manager, category, bundle):
        self.ensure_color_state(manager)
        group = self.bundle_group(bundle.get("name", ""), category)
        manager.context["color_plugin"]["bundle_groups"][bundle.get("name", "")] = group

    def format_status_hook(self, manager, default_text):
        self.ensure_color_state(manager)
        tracked = len(manager.context["color_plugin"]["bundle_groups"])
        return f"{default_text} | color-groups:{tracked}"

    def format_bundle_row_hook(self, manager, bundle, default_text):
        # Visual marker to make grouping readable even without color perception.
        group = self.bundle_group(bundle.get("name", ""), self.infer_category(bundle))
        tag = group.upper()
        return f"[{tag}] {default_text}"

    def format_file_row_hook(self, manager, file_data, default_text):
        # Keep file rows compact but still grouped.
        file_name = str(file_data.get("path", "")).lower()

        if file_name.endswith(".ini") or file_name.endswith(".xml") or file_name.endswith(".meta"):
            return f"[CFG] {default_text}"

        if file_name.endswith(".asi") or file_name.endswith(".dll"):
            return f"[BIN] {default_text}"

        return default_text

    def bundle_color_hook(self, manager, bundle):
        group = self.bundle_group(bundle.get("name", ""), self.infer_category(bundle))
        return self.group_colors(group)

    def file_color_hook(self, manager, file_data):
        name = str(file_data.get("path", "")).lower()

        if name.endswith(".ini") or name.endswith(".xml") or name.endswith(".meta"):
            return {"fg": "#ffd479"}

        if name.endswith(".asi") or name.endswith(".dll"):
            return {"fg": "#8ed0ff"}

        if name.endswith(".lua") or name.endswith(".cs") or name.endswith(".vb"):
            return {"fg": "#9bffb0"}

        return None

    def after_ui_action_hook(self, manager, *args):
        self.ensure_color_state(manager)
        manager.context["color_plugin"]["applied_rows"] += 1

    def bundle_group(self, name, category):
        lowered = name.lower()
        category = (category or "").lower()

        if lowered in self.CORE_MODS or any(key in lowered for key in self.LOADER_HINTS):
            return "core"

        if any(key in lowered for key in self.PERF_HINTS):
            return "perf"

        if any(key in lowered for key in self.GRAPHICS_HINTS):
            return "gfx"

        if category in {"scripts", "lspdfr"} or any(key in lowered for key in self.SCRIPT_HINTS):
            return "script"

        return "default"

    def group_colors(self, group):
        palette = {
            "core": {"fg": "#ff8f8f"},
            "perf": {"fg": "#ffd479"},
            "gfx": {"fg": "#9bd4ff"},
            "script": {"fg": "#a8ffbe"},
            "default": {"fg": "#f3f3f3"},
        }
        return palette.get(group, palette["default"])

    def infer_category(self, bundle):
        # Optional hint method so this plugin can evolve without core changes.
        files = bundle.get("files", [])
        for entry in files:
            path = str(entry.get("path", "")).lower()
            if "\\scripts\\" in path:
                return "scripts"
            if "\\lspdfr\\" in path:
                return "lspdfr"
        return "basegame"


Helper.plugin(Plugin)
