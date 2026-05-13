# Plugin System

Plugins live in `plugins/` and are loaded automatically from `.py` files. Bootstrap plugins live in `plugins/bootstrap/` or use the filename pattern `*_bootstrap.py`; they load before normal plugins and can prepare or extend the plugin manager itself.

Short cheat sheet for bootstrap/UI pipelines + permission card: see **`plugin-ui-pipelines.md`**.

## Basic Plugin

```python
from core.PluginManager import Helper, PluginBase


class Plugin(PluginBase):
    name = "My Plugin"
    version = "1.0.0"
    priority = 100
    supported_extensions = {".lua"}
    categories = ["Scripts"]

    def detect_category(self, manager, path):
        if path.suffix.lower() == ".lua":
            return "Scripts"


Helper.plugin(Plugin)
```

Plugins can also expose `register(manager)` and call `manager.register(...)` manually.
All plugins are now `Helper`-strict. Legacy plugins that are not marked with `Helper.plugin(...)` are rejected with warnings.

## Hook Layers

Every hook can be written in five forms:

```python
def hook_name(...): pass
def hook_name_hook(...): pass
def hook_name_process(...): pass
def hook_name_core(...): pass
def hook_name_internal(...): pass
```

Use `_hook` for public behavior, `_process` for data transformation, `_core` for app-level extension, and `_internal` for low-level manager behavior.

## Bootstrapping

Bootstrap plugins can modify `manager.context`, register helper plugins, or prepare shared services before regular plugins load.

Available bootstrap hooks:

- `plugin_manager_bootstrap`
- `before_plugins_loaded`
- `after_plugins_loaded`
- `before_plugin_loaded`
- `after_plugin_loaded`
- `on_plugin_registered`
- `on_plugin_error`

Each also supports `_hook`, `_process`, `_core`, and `_internal`.

## Bootstrap pipelines (`run_bootstrap_pipeline`)

After bootstrap `.py` files load (and again after normal plugins load), the manager runs named pipelines:

```python
manager.run_bootstrap_pipeline("permission", {"stage": "bootstrap", "reports": []})
```

Plugins participate by implementing callbacks whose prefix matches the pipeline name:

- `bootstrap_pipeline_<name>`
- `bootstrap_pipeline_<name>_hook`, `_process`, `_core`, `_internal`

Each receives `(manager, state)`. Return a **new or mutated `state`** dict/object to pass forward; `None` leaves state unchanged.

Stock pipeline: **`permission`** in `plugins/bootstrap/bootstrap_pipelines.py` — scans plugin sources for heuristic capability tags. Latest output also stored on `manager.context["permission_pipeline_last"]`.

## UI render pipeline (`run_ui_render_pipeline`)

Gui calls `manager.plugin_manager.run_ui_render_pipeline(manager, window, slot, context)` for fixed slots. Plugins implement:

- `ui_render(manager, window, slot, context)`
- or `ui_render_hook`, `_process`, `_core`, `_internal` with same signature

Allowed `slot` values: `toolbar`, `menu`, `sidebar`, `context_action`, `status_widget`, `detail`.

**Return value:** `None` (skip), a single contribution, or a list/tuple of contributions.

Examples:

```python
from PyQt5.QtWidgets import QMessageBox

def ui_render_hook(self, manager, window, slot, context):
    if slot != "toolbar":
        return None
    def _go():
        QMessageBox.information(window, "Demo", "Hello from plugin")
    return {"type": "action", "text": "Demo", "callback": _go}
```

```python
def ui_render_hook(self, manager, window, slot, context):
    if slot != "sidebar":
        return None
    lab = QLabel("Sidebar note")
    return {"widget": lab}
```

```python
def ui_render_hook(self, manager, window, slot, context):
    if slot != "context_action":
        return None
    return {
        "type": "action",
        "target": "bundle",  # or "file"
        "text": "Log bundle",
        "callback": lambda bundle: print(bundle["name"]),
    }
```

The main window merges toolbar/menu actions, embeds widgets in the plugin sidebar column, status row, and detail area, and attaches bundle/file context menus from `context_action` entries.

## Plugin permission scan & review UI

On each loaded non-bootstrap plugin file, the manager runs a **static** scan (`core/plugin_permissions.py`) and attaches **`__plugin_permission_report__`** on the plugin object (`permissions`, `dangerous`, etc.). This is heuristic text matching, not enforcement.

If the report is “interesting” (has permission tags **or** `dangerous == True`) **and** the resolved file path is not in `reviewed_plugin_paths` inside `gta5populator_config.json`, an item is queued in **`manager.context["plugin_review_queue"]`**. The desktop app shows a centered card (permissions summary + danger flag + path). **Got it** adds the path to `reviewed_plugin_paths` and persists config.

Bootstrap-only plugins are scanned by the **`permission`** pipeline but do not enqueue the review card on their own unless loaded as normal plugins.

## Debugger

The app has a PyQt5 plugin debugger in `core/debug/PluginDebugger.py`. Open it from the app with the `Debug` button.

It shows:

- Loaded plugins
- Versions
- Priorities
- Supported extensions
- Categories
- Hook coverage
- Bootstrap activity
- Live event codes
- Plugin errors and tracebacks
- Shared `manager.context`

Use `Reload Plugins` after editing plugin files. Use `Run Mock Hook` to call a selected hook with safe mock data and inspect what plugins do.

## Bootstrap Showcase

See `plugins/bootstrap/bootstrap_showcase.py` for a documented reference plugin that demonstrates self-expansion patterns:

- Initializes structured bootstrap context.
- Tracks bootstrap plugin file inventory.
- Dynamically registers a runtime helper plugin.
- Appends status info through a plugin hook.
- Annotates plugin errors with additional events.

Use this file as a template when building bootstrap plugins that evolve the manager or app behavior without editing core application code.

## Scanner Hooks

Plugins can change scanning without editing `app.py`:

- `before_scan(manager, initial)`
- `after_scan(manager, initial, grouped)`
- `normalize_file_path(manager, path, is_disabled)`
- `should_include_file(manager, path, actual_path)`
- `detect_category(manager, path)`
- `clean_bundle_name(manager, name)`
- `get_bundle_name(manager, path, actual_path, category)`
- `on_new_file_detected(manager, path)`
- `on_file_grouped(manager, path, category, bundle_name, file_data)`
- `after_bundle_built(manager, category, bundle)`

## File Action Hooks

- `before_toggle_bundle(manager, bundle, enabling)`
- `before_toggle_file(manager, path, enabling)`
- `after_toggle_file(manager, old_path, new_path, enabling)`
- `after_toggle_bundle(manager, bundle, enabling)`
- `before_disable_file(manager, path)`
- `after_disable_file(manager, old_path, new_path)`

## UI Hooks

- `on_ui_ready(manager, window)`
- `on_ui_refreshed(manager, window)`
- `on_bundle_selected(manager, bundle)`
- `on_bundle_double_click(manager, bundle)`
- `on_file_double_click(manager, file_data)`
- `format_bundle_row(manager, bundle, default_text)`
- `format_file_row(manager, file_data, default_text)`
- `format_status(manager, default_text)`
- `bundle_color(manager, bundle)`
- `file_color(manager, file_data)`

Color hooks can return:
- `"#RRGGBB"` for foreground color
- `(fg, bg)` tuple such as `("#ffffff", "#2a2a2a")`
- `{"fg": "#ffffff", "bg": "#2a2a2a"}`

Compatibility support is built in for plugin manager/app manager differences:
- `manager.context` is available in runtime hooks
- `manager.aliases()` is supported
- `file_data` includes both `active` and legacy `disabled`

## Plugin Data

Plugins can define:

- `supported_extensions`
- `categories`
- `ignored_stems`
- `ignored_parent_names`
- `aliases`
- `priority`

Higher priority numbers run later and can override earlier plugins in `first_result()` hooks.

## Current Use Cases

You can add support for new file types, create new categories, override bundle naming, add UI actions, open files or folders, track scan results, change status text, register **toolbar/menu/sidebar/status/detail/context menu** contributions via `ui_render`, run shared **bootstrap pipelines** (e.g. permission inventory), or add future app features without changing most of `app.py`.
