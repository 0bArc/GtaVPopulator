import importlib.util
import os
import traceback

from pathlib import Path
from collections import defaultdict

from core.plugin_permissions import analyze_python_plugin_source


class Helper:
    """
    Runtime patch helper.

    Usage:
        from core.PluginManager import Helper, PluginBase

        @Helper.patch(PluginBase._file_process)
        def my_patch(value, context):
            return value
    """

    _patches = defaultdict(list)
    _strict = True

    

    @classmethod
    def patch(cls, hook_name):
        hook_name = str(hook_name)

        def decorator(func):
            cls._patches[hook_name].append(func)
            return func

        return decorator

    @classmethod
    def run(cls, hook_name, value, context):
        result = value

        for func in cls._patches.get(str(hook_name), []):
            updated = func(result, context)

            if updated is not None:
                result = updated

        return result

    @classmethod
    def plugin(cls, obj):
        setattr(obj, "__helper_plugin__", True)
        return obj


class PluginBase:
    name = "Unnamed Plugin"
    version = "1.0.0"
    description = "No description provided"
    author = "Team Stratware"
    priority = 100
    supported_extensions = set()
    categories = set()
    ignored_stems = set()
    ignored_parent_names = set()
    aliases = {}

    def plugin_manager_bootstrap_hook(self, plugin_manager):
        pass

    def plugin_manager_bootstrap_process(self, plugin_manager):
        pass

    def plugin_manager_bootstrap_core(self, plugin_manager):
        pass

    def plugin_manager_bootstrap_internal(self, plugin_manager):
        pass

    def before_plugins_loaded_hook(self, plugin_manager):
        pass

    def after_plugins_loaded_hook(self, plugin_manager):
        pass

    def before_plugin_loaded_hook(self, plugin_manager, plugin_file):
        pass

    def after_plugin_loaded_hook(self, plugin_manager, plugin):
        pass

    def on_plugin_registered_hook(self, plugin_manager, plugin):
        pass

    def on_plugin_error_hook(self, plugin_manager, error):
        pass

    def on_app_start(self, app):
        pass

    def on_config_loaded(self, manager, data):
        pass

    def on_config_saving(self, manager, data):
        pass

    def on_folder_added(self, manager, path):
        pass

    def on_folder_removed(self, manager, path):
        pass

    def before_scan(self, manager, initial):
        pass

    def after_scan(self, manager, initial, grouped):
        pass

    def normalize_file_path(self, manager, path, is_disabled):
        return None

    def should_include_file(self, manager, path, actual_path):
        return None

    def detect_category(self, manager, path):
        return None

    def clean_bundle_name(self, manager, name):
        return None

    def get_bundle_name(self, manager, path, actual_path, category):
        return None

    def on_new_file_detected(self, manager, path):
        pass

    def on_file_grouped(self, manager, path, category, bundle_name, file_data):
        pass

    def after_bundle_built(self, manager, category, bundle):
        pass

    def before_toggle_bundle(self, manager, bundle, enabling):
        pass

    def before_toggle_file(self, manager, path, enabling):
        pass

    def after_toggle_file(self, manager, old_path, new_path, enabling):
        pass

    def after_toggle_bundle(self, manager, bundle, enabling):
        pass

    def before_disable_file(self, manager, path):
        pass

    def after_disable_file(self, manager, old_path, new_path):
        pass

    def on_ui_ready(self, manager, window):
        pass

    def on_ui_refreshed(self, manager, window):
        pass

    def on_bundle_selected(self, manager, bundle):
        pass

    def on_bundle_double_click(self, manager, bundle):
        pass

    def on_file_double_click(self, manager, file_data):
        pass

    def format_bundle_row(self, manager, bundle, default_text):
        return None

    def format_file_row(self, manager, file_data, default_text):
        return None

    def format_status(self, manager, default_text):
        return None

    def bootstrap_pipeline_hook(self, plugin_manager, state):
        return None

    def ui_render(self, manager, window, slot, context):
        return None

    def ui_render_hook(self, manager, window, slot, context):
        return None

    def ui_render_process(self, manager, window, slot, context):
        return None

    def ui_render_core(self, manager, window, slot, context):
        return None

    def ui_render_internal(self, manager, window, slot, context):
        return None

    def get_bundle_info(self, manager, bundle):
        return None

    def bundle_color(self, manager, bundle):
        return None

    def file_color(self, manager, file_data):
        return None

    # Helper.patch targets (string values match callback_names / Helper.run keys)
    _bundle_color = "bundle_color"
    _file_color = "file_color"

    def extension_point(self, manager, area, phase, *args, **kwargs):
        return None

    def extension_point_hook(self, manager, area, phase, *args, **kwargs):
        return None

    def extension_point_process(self, manager, area, phase, *args, **kwargs):
        return None

    def extension_point_core(self, manager, area, phase, *args, **kwargs):
        return None

    def extension_point_internal(self, manager, area, phase, *args, **kwargs):
        return None



def _noop(*args, **kwargs):
    return None


_EXTRA_HOOK_STEMS = (
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
)

for _stem in _EXTRA_HOOK_STEMS:
    setattr(PluginBase, _stem, _noop)
    setattr(PluginBase, f"{_stem}_hook", _noop)
    setattr(PluginBase, f"{_stem}_process", _noop)
    setattr(PluginBase, f"{_stem}_core", _noop)
    setattr(PluginBase, f"{_stem}_internal", _noop)
    setattr(PluginBase, f"_{_stem}", _stem)
    setattr(PluginBase, f"_{_stem}_hook", f"{_stem}_hook")
    setattr(PluginBase, f"_{_stem}_process", f"{_stem}_process")
    setattr(PluginBase, f"_{_stem}_core", f"{_stem}_core")
    setattr(PluginBase, f"_{_stem}_internal", f"{_stem}_internal")


class BuiltInGtaPlugin(PluginBase):
    name = "Built-in GTA V Support"
    version = "1.0.0"
    supported_extensions = {".dll", ".asi", ".ini", ".cs", ".vb"}
    categories = ["BaseGame", "Scripts", "Plugins", "LSPDFR"]
    ignored_stems = {
        "dinput8",
        "zlib1",
        "xinput1_4",
        "version",
        "dsound",
        "vcruntime140",
        "msvcp140",
        "opus",
        "opusenc",
        "xlive",
    }
    ignored_parent_names = {
        "scripts",
        "plugins",
        "asi",
        "lspdfr",
        "grand theft auto v",
        "grand theft auto v legacy",
    }
    aliases = {
        "scripthookv": "ScriptHookV",
        "scripthookvdotnet": "ScriptHookVDotNet",
        "scripthookvdotnet2": "ScriptHookVDotNet",
        "scripthookvdotnet3": "ScriptHookVDotNet",
        "packfilelimitadjuster": "PackFileLimitAdjuster",
        "weaponlimitsadjuster": "WeaponLimitsAdjuster",
        "heapadjuster": "HeapAdjuster",
        "poolmanager": "PoolManager",
        "ragepluginhook": "RagePluginHook",
        "openiv": "OpenIV",
    }

    def detect_category(self, manager, path):
        lower = str(path).replace("/", "\\").lower()

        if "\\lspdfr\\" in lower:
            return "LSPDFR"

        if "\\scripts\\" in lower:
            return "Scripts"

        if "\\plugins\\" in lower:
            return "Plugins"

        return "BaseGame"


Helper.plugin(BuiltInGtaPlugin)


class PluginManager:
    def __init__(self, plugin_folder="plugins", reviewed_plugin_paths=None):
        self.plugin_folder = Path(plugin_folder)
        self.bootstrap_folder = self.plugin_folder / "bootstrap"
        self.plugins = []
        self.errors = []
        self.event_log = []
        self.context = {}
        self.loaded_files = set()
        self._loaded_modules = set()
        self._executed_hooks = set()
        self._callback_cache = {}
        self._callback_name_cache = {}
        self._event_index = 0
        self._event_log_max = 1000
        self._verbose_events = os.environ.get("GTA_POPULATOR_VERBOSE_EVENTS") == "1"
        self._scan_plugin_sources_on_load = (
            os.environ.get("GTA_POPULATOR_SCAN_PLUGINS_ON_LOAD") == "1"
        )
        self.reviewed_plugin_paths = reviewed_plugin_paths
        if self.reviewed_plugin_paths is None:
            self.reviewed_plugin_paths = set()
        self.bootstrap()
        self.register(BuiltInGtaPlugin())
        self.load_plugins()

    def bootstrap(self):
        self.log_event("BOOTSTRAP_START", "Loading bootstrap plugins")
        self.plugin_folder.mkdir(parents=True, exist_ok=True)
        self.bootstrap_folder.mkdir(parents=True, exist_ok=True)

        for plugin_file in self.bootstrap_files():
            self.load_plugin_file(plugin_file, bootstrap=True)

        self.run_bootstrap_pipeline("permission", {"stage": "bootstrap", "reports": []})
        self.hook("plugin_manager_bootstrap", self)
        self.log_event("BOOTSTRAP_DONE", "Bootstrap complete")

    def register(self, plugin):
        if isinstance(plugin, type):
            plugin = plugin()

        if Helper._strict and not getattr(plugin, "__helper_plugin__", False):
            self.add_error(
                {
                    "plugin": getattr(plugin, "name", plugin.__class__.__name__),
                    "hook": "register",
                    "error": "Legacy plugin rejected: use Helper.plugin(...) on plugin class/instance",
                    "traceback": "",
                }
            )
            self.log_event(
                "PLUGIN_REJECTED_LEGACY",
                "Legacy plugin rejected",
                plugin=getattr(plugin, "name", plugin.__class__.__name__),
            )
            return None

        self.plugins.append(plugin)
        self.plugins.sort(key=lambda item: getattr(item, "priority", 100))
        self._callback_cache.clear()
        self.log_event(
            "PLUGIN_REGISTERED",
            getattr(plugin, "name", plugin.__class__.__name__),
            plugin=getattr(plugin, "name", plugin.__class__.__name__),
            priority=getattr(plugin, "priority", 100),
            version=getattr(plugin, "version", ""),
        )
        self.hook("on_plugin_registered", self, plugin)

        return plugin

    def load_plugins(self):
        self.plugin_folder.mkdir(parents=True, exist_ok=True)
        self.log_event("PLUGIN_LOAD_START", "Loading normal plugins")
        self.hook("before_plugins_loaded", self)

        for plugin_file in self.plugin_files():
            if plugin_file.name.startswith("_"):
                continue

            self.load_plugin_file(plugin_file)

        self.hook("after_plugins_loaded", self)
        self.run_bootstrap_pipeline("permission", {"stage": "after_load", "reports": []})
        self.log_event("PLUGIN_LOAD_DONE", "Plugin loading complete")

    def bootstrap_files(self):
        files = list(self.bootstrap_folder.glob("*.py"))
        files.extend(self.plugin_folder.glob("*_bootstrap.py"))
        return sorted(set(files))

    def plugin_files(self):
        bootstrap_files = {
            path.resolve()
            for path in self.bootstrap_files()
        }

        return [
            path
            for path in sorted(self.plugin_folder.rglob("*.py"))
            if path.resolve() not in bootstrap_files
            and self.bootstrap_folder not in path.parents
            and not path.name.startswith("_")
            and path.name != "__init__.py"
        ]

    def load_plugin_file(self, plugin_file, bootstrap=False):
        import importlib.util
        import sys
        import traceback
        from pathlib import Path

        plugin_file = Path(plugin_file)
        module_id = str(plugin_file.resolve())

        # No double dipping: already processed this file once
        if module_id in self.loaded_files:
            self.log_event("PLUGIN_SKIPPED", str(plugin_file), file=str(plugin_file))
            return None

        relative = plugin_file.relative_to(self.plugin_folder)

        module_name = (
            "gta_populator_" +
            "_".join(relative.with_suffix("").parts)
        )

        # Already living in the runtime? Then we do not wake it again
        if module_name in sys.modules:
            self.log_event("PLUGIN_SKIPPED", str(plugin_file), file=str(plugin_file))
            self.loaded_files.add(module_id)
            return sys.modules[module_name]

        try:
            self.log_event(
                "PLUGIN_FILE_LOADING",
                str(plugin_file),
                file=str(plugin_file),
                bootstrap=bootstrap,
            )

            if not bootstrap:
                self.hook("before_plugin_loaded", self, plugin_file)

            spec = importlib.util.spec_from_file_location(module_name, plugin_file)

            if spec is None or spec.loader is None:
                raise ImportError(f"Could not load plugin spec for {plugin_file}")

            module = importlib.util.module_from_spec(spec)

            # We register it early so Python does not accidentally load it twice mid-flight
            sys.modules[module_name] = module

            # Mark as loaded before execution so recursion does not bite us later
            self.loaded_files.add(module_id)

            # Let the module breathe and execute its code once
            spec.loader.exec_module(module)

            if getattr(module, "isEnabled", True) is False:
                self.log_event("PLUGIN_DISABLED", str(plugin_file), file=str(plugin_file))
                return None

            has_plugin_class = hasattr(module, "Plugin")
            has_register = hasattr(module, "register")

            has_helper_patches = any(
                getattr(value, "__module__", None) == module.__name__
                for value in vars(module).values()
                if callable(value)
            )

            if has_register:
                module.register(self)
                plugin = module

            elif has_plugin_class:
                plugin = self.register(module.Plugin)

            elif has_helper_patches:
                plugin = module

            else:
                raise AttributeError(
                    "Plugin file must define register(manager), Plugin, or Helper patches"
                )

            if plugin is not None:
                setattr(plugin, "__plugin_file__", str(plugin_file))
                setattr(plugin, "__plugin_bootstrap__", bootstrap)

                if not bootstrap and self._scan_plugin_sources_on_load:
                    report = analyze_python_plugin_source(plugin_file)
                    setattr(plugin, "__plugin_permission_report__", report)
                    key = str(plugin_file.resolve())
                    perms = report.get("permissions") or []
                    interesting = bool(report.get("dangerous")) or bool(perms)

                    if interesting and key not in self.reviewed_plugin_paths:
                        queue = self.context.setdefault("plugin_review_queue", [])
                        if not any(entry.get("path") == key for entry in queue):
                            queue.append(
                                {
                                    "path": key,
                                    "file": str(plugin_file),
                                    "plugin_name": getattr(
                                        plugin, "name", plugin.__class__.__name__
                                    ),
                                    "report": report,
                                }
                            )

            self.log_event(
                "PLUGIN_FILE_LOADED",
                str(plugin_file),
                file=str(plugin_file),
                bootstrap=bootstrap,
                plugin=getattr(plugin, "name", getattr(plugin, "__name__", str(plugin))),
            )

            if not bootstrap:
                self.hook("after_plugin_loaded", self, plugin)

            return plugin

        except Exception as exc:
            self.add_error(
                {
                    "plugin": str(plugin_file),
                    "error": str(exc),
                    "traceback": traceback.format_exc(),
                }
            )
            return None

    def hook(self, hook_name, *args, **kwargs):
        results = []

        for plugin, callback_name in self.callbacks_for(hook_name):
            result = self.call_plugin(plugin, callback_name, *args, **kwargs)

            if result is not None:
                results.append(result)

        for callback_name in self.helper_patch_names(hook_name):
            result = self.run_helper_patch(callback_name, None, *args, **kwargs)

            if result is not None:
                results.append(result)

        return results

    def hook_extension(self, manager, area, phase, *args, **kwargs):
        results = []

        for plugin, callback_name in self.callbacks_for("extension_point"):
            result = self.call_plugin(
                plugin, callback_name, manager, area, phase, *args, **kwargs
            )

            if result is not None:
                results.append(result)

        return results

    def first_result(self, hook_name, *args, **kwargs):
        callbacks = self.callbacks_for(hook_name, reverse=True)
        ran_helper_patches = set()

        if hook_name in Helper._patches and not any(
            callback_name == hook_name for _, callback_name in callbacks
        ):
            result = self.run_helper_patch(hook_name, None, *args, **kwargs)
            ran_helper_patches.add(hook_name)

            if result is not None:
                return result

        for plugin, callback_name in callbacks:
            result = self.call_plugin(plugin, callback_name, *args, **kwargs)

            if result is not None:
                return result

        for callback_name in self.helper_patch_names(hook_name):
            if callback_name in ran_helper_patches:
                continue

            result = self.run_helper_patch(callback_name, None, *args, **kwargs)

            if result is not None:
                return result

        return None

    def callback_names(self, hook_name):
        cached = self._callback_name_cache.get(hook_name)

        if cached is not None:
            return cached

        names = [hook_name]

        for suffix in ("hook", "process", "core", "internal"):
            names.append(f"{hook_name}_{suffix}")

        names = tuple(names)
        self._callback_name_cache[hook_name] = names
        return names

    def callbacks_for(self, hook_name, reverse=False):
        key = (hook_name, reverse)
        cached = self._callback_cache.get(key)

        if cached is not None:
            return cached

        plugins = reversed(self.plugins) if reverse else self.plugins
        callbacks = []

        for plugin in plugins:
            for callback_name in self.callback_names(hook_name):
                if self.has_callback(plugin, callback_name):
                    callbacks.append((plugin, callback_name))

        callbacks = tuple(callbacks)
        self._callback_cache[key] = callbacks
        return callbacks

    def has_callback(self, plugin, callback_name):
        plugin_dict = getattr(plugin, "__dict__", {})

        if callback_name in plugin_dict:
            return callable(plugin_dict.get(callback_name))

        plugin_class = getattr(plugin, "__class__", None)

        if plugin_class is not None and callback_name in getattr(plugin_class, "__dict__", {}):
            return callable(getattr(plugin, callback_name, None))

        return False

    def helper_patch_names(self, hook_name):
        return [
            callback_name
            for callback_name in self.callback_names(hook_name)
            if callback_name in Helper._patches
        ]

    def run_helper_patch(self, callback_name, result, *args, **kwargs):
        return Helper.run(
            callback_name,
            result,
            {
                "plugin_manager": self,
                "plugin": None,
                "callback": callback_name,
                "args": args,
                "kwargs": kwargs,
            },
        )

    def call_plugin(self, plugin, callback_name, *args, **kwargs):
        callback = getattr(plugin, callback_name, None)
 
        if not callable(callback):
            return None

        try:
            result = callback(*args, **kwargs)
            result = Helper.run(
                callback_name,
                result,
                {
                    "plugin_manager": self,
                    "plugin": plugin,
                    "callback": callback_name,
                    "args": args,
                    "kwargs": kwargs,
                },
            )

            return result
        except Exception as exc:
            self.add_error(
                {
                    "plugin": getattr(plugin, "name", plugin.__class__.__name__),
                    "hook": callback_name,
                    "error": str(exc),
                    "traceback": traceback.format_exc(),
                }
            )

        return None

    def add_error(self, error):
        self.errors.append(error)
        self.log_event(
            "ERROR",
            error.get("error", "Plugin error"),
            plugin=error.get("plugin", ""),
            hook=error.get("hook", ""),
        )

        if error.get("hook") == "on_plugin_error_hook":
            return

        self.hook("on_plugin_error", self, error)

    def log_event(self, code, message, **data):
        noisy_codes = {
            "HOOK_START",
            "HOOK_DONE",
            "HOOK_EXTENSION_START",
            "HOOK_EXTENSION_DONE",
            "FIRST_RESULT_START",
            "FIRST_RESULT_FOUND",
            "FIRST_RESULT_EMPTY",
            "CALL",
            "CALL_RESULT",
        }

        if not self._verbose_events and code in noisy_codes:
            return

        self._event_index += 1
        self.event_log.append(
            {
                "index": self._event_index,
                "code": code,
                "message": message,
                "data": data,
            }
        )

        overflow = len(self.event_log) - self._event_log_max

        if overflow > 0:
            del self.event_log[:overflow]

    def supported_extensions(self):
        extensions = set()

        for plugin in self.plugins:
            extensions.update(getattr(plugin, "supported_extensions", set()) or set())

        return {extension.lower() for extension in extensions}

    def categories(self):
        categories = []

        for plugin in self.plugins:
            for category in getattr(plugin, "categories", set()) or set():
                if category not in categories:
                    categories.append(category)

        return categories or ["BaseGame", "Scripts", "Plugins", "LSPDFR"]

    def ignored_stems(self):
        stems = set()

        for plugin in self.plugins:
            stems.update(getattr(plugin, "ignored_stems", set()) or set())

        return {stem.lower() for stem in stems}

    def ignored_parent_names(self):
        names = set()

        for plugin in self.plugins:
            names.update(getattr(plugin, "ignored_parent_names", set()) or set())

        return {name.lower() for name in names}

    def aliases(self):
        aliases = {}

        for plugin in self.plugins:
            aliases.update(getattr(plugin, "aliases", {}) or {})

        return aliases

    def run_bootstrap_pipeline(self, pipeline_name, initial_state=None):
        state = initial_state
        prefix = f"bootstrap_pipeline_{pipeline_name}"

        for plugin, callback_name in self.callbacks_for(prefix):
            result = self.call_plugin(plugin, callback_name, self, state)

            if result is not None:
                state = result

        self.log_event(
            "BOOTSTRAP_PIPELINE_DONE",
            prefix,
            pipeline=pipeline_name,
        )
        return state

    def run_ui_render_pipeline(self, manager, window, slot, context=None):
        allowed = {
            "toolbar",
            "menu",
            "sidebar",
            "context_action",
            "status_widget",
            "detail",
        }

        if slot not in allowed:
            raise ValueError(f"Unknown ui_render slot: {slot}")

        ctx = dict(context or {})
        collected = []

        for plugin, callback_name in self.callbacks_for("ui_render"):
            result = self.call_plugin(
                plugin, callback_name, manager, window, slot, ctx
            )

            if not result:
                continue

            if isinstance(result, (list, tuple)):
                collected.extend(result)
            else:
                collected.append(result)

        return collected
