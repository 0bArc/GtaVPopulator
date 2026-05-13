"""
Bootstrap Showcase Plugin
=========================

Purpose:
Demonstrate how a bootstrap plugin can expand the plugin system from inside the
plugin layer, without changing the main app or PluginManager implementation.

What this file showcases:
1) Early context initialization during bootstrap.
2) Dynamic registration of a helper plugin at runtime.
3) Event enrichment for diagnostics and onboarding.
4) Inline documentation patterns for future plugin authors.
"""

from core.PluginManager import Helper, PluginBase


class RuntimeShowcaseHelper(PluginBase):
    """
    Runtime helper plugin registered by the bootstrap plugin itself.

    This proves bootstrap code can add new plugin behavior dynamically.
    """

    name = "Runtime Showcase Helper"
    version = "1.0.0"
    priority = 220

    def on_plugin_registered_hook(self, manager, plugin):
        # Skip logging registration of this helper itself to avoid noisy recursion.
        if plugin is self:
            return

        registry = manager.context.setdefault("showcase", {}).setdefault(
            "runtime_registered_plugins", []
        )
        registry.append(getattr(plugin, "name", plugin.__class__.__name__))

    def format_status_hook(self, manager, default_text):
        """
        Lightweight UI extension:
        Appends plugin count to status text without modifying app.py.
        """
        return f"{default_text} | plugins: {len(manager.plugin_manager.plugins)}"


class Plugin(PluginBase):
    """
    Main bootstrap showcase plugin.
    """

    name = "Bootstrap Showcase"
    version = "1.0.0"
    priority = 25

    def plugin_manager_bootstrap_hook(self, manager):
        """
        Runs during bootstrap stage.

        We initialize a dedicated context bucket used by this showcase.
        """
        manager.context.setdefault(
            "showcase",
            {
                "bootstrap_runs": 0,
                "loaded_files": [],
                "runtime_helper_registered": False,
                "runtime_registered_plugins": [],
                "hook_samples": [],
            },
        )

        manager.context["showcase"]["bootstrap_runs"] += 1

    def plugin_manager_bootstrap_process(self, manager):
        """
        Example of *_process layer:
        Track bootstrap files for traceability and debugger visibility.
        """
        files = [str(path) for path in manager.bootstrap_files()]
        manager.context["showcase"]["loaded_files"] = files

        manager.log_event(
            "SHOWCASE_BOOTSTRAP_FILES",
            "Tracked bootstrap file inventory",
            files=len(files),
        )

    def plugin_manager_bootstrap_core(self, manager):
        """
        Example of *_core layer:
        Dynamically register helper plugin behavior from bootstrap context.
        """
        showcase = manager.context["showcase"]

        if showcase.get("runtime_helper_registered"):
            return

        manager.register(RuntimeShowcaseHelper())
        showcase["runtime_helper_registered"] = True

        manager.log_event(
            "SHOWCASE_HELPER_REGISTERED",
            "Runtime helper registered by bootstrap showcase",
            plugin=RuntimeShowcaseHelper.name,
        )

    def after_plugin_loaded_hook(self, manager, plugin):
        """
        Record plugin file mapping to demonstrate post-load introspection.
        """
        plugin_name = getattr(plugin, "name", getattr(plugin, "__name__", str(plugin)))
        plugin_file = getattr(plugin, "__plugin_file__", "unknown")

        manager.context["showcase"]["hook_samples"].append(
            f"after_plugin_loaded -> {plugin_name} ({plugin_file})"
        )

    def on_plugin_error_hook(self, manager, error):
        """
        Demonstrate custom error annotation without interrupting core behavior.
        """
        manager.log_event(
            "SHOWCASE_ERROR_ANNOTATION",
            "Showcase observed plugin error",
            plugin=error.get("plugin", ""),
            hook=error.get("hook", ""),
        )


Helper.plugin(RuntimeShowcaseHelper)
Helper.plugin(Plugin)
