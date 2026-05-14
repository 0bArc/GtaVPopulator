"""
Finite hook catalog for runtime + debugger (no cartesian explosion).

- `DECLARED_HOOK_NAMES` — hooks the app / manager may invoke via `hook()` / `first_result()`.
- `extension_point` — optional `(area, phase)` grid; call `PluginManager.hook_extension(...)`.
"""

EXTENSION_AREAS = (
    "app",
    "plugin",
    "bootstrap",
    "config",
    "path",
    "scan",
    "category",
    "bundle",
    "file",
    "toggle",
    "status",
    "ui",
    "debug",
    "search",
    "filter",
    "sort",
    "dependency",
    "metrics",
    "cache",
    "render",
)

EXTENSION_PHASES = (
    "prepare",
    "validate",
    "process",
    "enrich",
    "normalize",
    "before",
    "after",
    "finalize",
)

FIRST_RESULT_HOOKS = frozenset(
    {
        "normalize_file_path",
        "should_include_file",
        "detect_category",
        "clean_bundle_name",
        "get_bundle_name",
        "format_bundle_row",
        "format_file_row",
        "format_status",
        "get_bundle_info",
        "bundle_color",
        "file_color",
    }
)

DECLARED_HOOK_NAMES = tuple(
    sorted(
        {
            "plugin_manager_bootstrap",
            "before_plugins_loaded",
            "after_plugins_loaded",
            "before_plugin_loaded",
            "after_plugin_loaded",
            "on_plugin_registered",
            "on_plugin_error",
            "on_app_start",
            "on_config_loaded",
            "on_config_saving",
            "on_folder_added",
            "on_folder_removed",
            "before_scan",
            "after_scan",
            "normalize_file_path",
            "should_include_file",
            "detect_category",
            "clean_bundle_name",
            "get_bundle_name",
            "on_new_file_detected",
            "on_file_grouped",
            "after_bundle_built",
            "before_toggle_bundle",
            "before_toggle_file",
            "after_toggle_file",
            "after_toggle_bundle",
            "before_disable_file",
            "after_disable_file",
            "on_ui_ready",
            "on_ui_refreshed",
            "on_bundle_selected",
            "on_bundle_double_click",
            "on_file_double_click",
            "format_bundle_row",
            "format_file_row",
            "format_status",
            "get_bundle_info",
            "bundle_color",
            "file_color",
            "row_render_process",
            "row_render_bundle_process",
            "row_render_file_process",
            "before_action",
            "after_action",
            "before_ui_action",
            "after_ui_action",
            "before_scan_action",
            "after_scan_action",
            "before_toggle_action",
            "after_toggle_action",
            "extension_point",
            "ui_render",
        }
    )
)


def discover_bootstrap_pipeline_methods(plugin):
    """Return pipeline name strings for methods bootstrap_pipeline_<name>_hook etc."""
    names = set()
    for key in dir(type(plugin)):
        if not key.startswith("bootstrap_pipeline_"):
            continue
        for suffix in ("_hook", "_process", "_core", "_internal"):
            if key.endswith(suffix):
                inner = key[len("bootstrap_pipeline_") : -len(suffix)]
                if inner:
                    names.add(inner)
                break
    return sorted(names)


def discover_ui_render_methods(plugin):
    """Return pipeline name strings for methods ui_render_<name>_hook etc."""
    names = set()
    for key in dir(type(plugin)):
        if not key.startswith("ui_render_"):
            continue
        for suffix in ("_hook", "_process", "_core", "_internal"):
            if key.endswith(suffix):
                inner = key[len("ui_render_") : -len(suffix)]
                if inner:
                    names.add(inner)
                break
    return sorted(names)

