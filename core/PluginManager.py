import importlib.util
import traceback

from pathlib import Path
from collections import defaultdict


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
    
    def get_bundle_info(self, manager, bundle):
        return None

    def bundle_color(self, manager, bundle):
        return None

    def file_color(self, manager, file_data):
        return None
    
    


def _noop(*args, **kwargs):
    return None


_HOOK_BASE_AREAS = [
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
]

_HOOK_BASE_PHASES = [
    "prepare",
    "validate",
    "process",
    "enrich",
    "normalize",
    "before",
    "after",
    "finalize",
]

_HOOK_NAMES = [f"{area}_{phase}" for area in _HOOK_BASE_AREAS for phase in _HOOK_BASE_PHASES]
_HOOK_NAMES.extend(
    [
        "file_color",
        "bundle_color",
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
    ]
)

for _name in _HOOK_NAMES:
    # autosuggest-friendly identifiers for patching
    setattr(PluginBase, f"_{_name}", _name)
    setattr(PluginBase, f"_{_name}_hook", f"{_name}_hook")
    setattr(PluginBase, f"_{_name}_process", f"{_name}_process")
    setattr(PluginBase, f"_{_name}_core", f"{_name}_core")
    setattr(PluginBase, f"_{_name}_internal", f"{_name}_internal")

    # callable stubs for plugin implementations
    if not hasattr(PluginBase, _name):
        setattr(PluginBase, _name, _noop)
    setattr(PluginBase, f"{_name}_hook", _noop)
    setattr(PluginBase, f"{_name}_process", _noop)
    setattr(PluginBase, f"{_name}_core", _noop)
    setattr(PluginBase, f"{_name}_internal", _noop)


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
    def __init__(self, plugin_folder="plugins"):
        self.plugin_folder = Path(plugin_folder)
        self.bootstrap_folder = self.plugin_folder / "bootstrap"
        self.plugins = []
        self.errors = []
        self.event_log = []
        self.context = {}
        self.loaded_files = set()
        self._loaded_modules = set()
        self._executed_hooks = set()
        self.bootstrap()
        self.register(BuiltInGtaPlugin())
        self.load_plugins()

    def bootstrap(self):
        self.log_event("BOOTSTRAP_START", "Loading bootstrap plugins")
        self.plugin_folder.mkdir(parents=True, exist_ok=True)
        self.bootstrap_folder.mkdir(parents=True, exist_ok=True)

        for plugin_file in self.bootstrap_files():
            self.load_plugin_file(plugin_file, bootstrap=True)

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
        self.log_event("HOOK_START", hook_name, hook=hook_name)

        for plugin in self.plugins:
            for callback_name in self.callback_names(hook_name):
                result = self.call_plugin(plugin, callback_name, *args, **kwargs)

                if result is not None:
                    results.append(result)

        self.log_event("HOOK_DONE", hook_name, hook=hook_name, results=len(results))
        return results

    def first_result(self, hook_name, *args, **kwargs):
        self.log_event("FIRST_RESULT_START", hook_name, hook=hook_name)

        for plugin in reversed(self.plugins):
            for callback_name in self.callback_names(hook_name):
                result = self.call_plugin(plugin, callback_name, *args, **kwargs)

                if result is not None:
                    self.log_event(
                        "FIRST_RESULT_FOUND",
                        hook_name,
                        hook=hook_name,
                        callback=callback_name,
                        plugin=getattr(plugin, "name", plugin.__class__.__name__),
                        result=repr(result),
                    )
                    return result

        self.log_event("FIRST_RESULT_EMPTY", hook_name, hook=hook_name)
        return None

    def callback_names(self, hook_name):
        names = [hook_name]

        for suffix in ("hook", "process", "core", "internal"):
            names.append(f"{hook_name}_{suffix}")

        return names

    def call_plugin(self, plugin, callback_name, *args, **kwargs):
        callback = getattr(plugin, callback_name, None)
 
        if not callable(callback):
            return None

        try:
            self.log_event(
                "CALL",
                callback_name,
                plugin=getattr(plugin, "name", plugin.__class__.__name__),
                callback=callback_name,
            )
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

            if result is not None:
                self.log_event(
                    "CALL_RESULT",
                    callback_name,
                    plugin=getattr(plugin, "name", plugin.__class__.__name__),
                    callback=callback_name,
                    result=repr(result),
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
        self.event_log.append(
            {
                "index": len(self.event_log) + 1,
                "code": code,
                "message": message,
                "data": data,
            }
        )

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
