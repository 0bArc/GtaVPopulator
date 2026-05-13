import time
from core.PluginManager import Helper


class Plugin:
    name = "Debug Bootstrap"
    version = "1.0.0"

    def plugin_manager_bootstrap_hook(self, manager):
        manager.context["debug"] = {
            "plugin_load_times": {},
            "hook_calls": [],
            "slow_hooks": [],
        }

    def before_plugin_loaded_hook(self, manager, plugin_file):
        manager.context.setdefault("_plugin_timers", {})
        manager.context["_plugin_timers"][str(plugin_file)] = time.time()

    def after_plugin_loaded_hook(self, manager, plugin):
        timers = manager.context.get("_plugin_timers", {})

        plugin_name = getattr(plugin, "name", str(plugin))
        plugin_file = getattr(plugin, "__plugin_file__", plugin_name)

        start = timers.get(str(plugin_file))

        if start is None:
            return

        elapsed = round(time.time() - start, 4)

        manager.context["debug"]["plugin_load_times"][
            plugin_name
        ] = elapsed

        manager.log_event(
            "BOOTSTRAP_PLUGIN_TIMED",
            f"Loaded {plugin_name} in {elapsed}s",
            plugin=plugin_name,
            elapsed=elapsed,
        )

    def on_plugin_error_hook(self, manager, error):
        manager.log_event(
            "BOOTSTRAP_PLUGIN_ERROR",
            error.get("error", "Plugin error"),
            plugin=error.get("plugin"),
            hook=error.get("hook"),
        )


Helper.plugin(Plugin)
