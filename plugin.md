# Plugin System

Plugins live in `plugins/` and are loaded automatically from `.py` files. Bootstrap plugins live in `plugins/bootstrap/` or use the filename pattern `*_bootstrap.py`; they load before normal plugins and can prepare or extend the plugin manager itself.

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

You can add support for new file types, create new categories, override bundle naming, add UI actions, open files or folders, track scan results, change status text, or add future app features without changing most of `app.py`.
