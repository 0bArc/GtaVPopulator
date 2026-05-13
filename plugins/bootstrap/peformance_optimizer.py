from core.PluginManager import Helper, PluginBase


class Plugin(PluginBase):
    name = "Performance Internals"
    version = "0.2.0"
    author = "Team Stratware"

    description = (
        "Bootstrap runtime optimizer for "
        "plugin dispatching and Qt UI updates."
    )

    priority = -100

    def plugin_manager_bootstrap(self, plugin_manager):
        """
        Install optimized dispatch pipeline.
        """

        plugin_manager.context.setdefault(
            "performance",
            {}
        )

        performance = plugin_manager.context["performance"]

        performance.update(
            {
                "cached_hooks": 0,
                "fast_calls": 0,
            }
        )

        #
        # CALLBACK NAME CACHE
        #

        callback_name_cache = {}

        original_callback_names = plugin_manager.callback_names

        def cached_callback_names(hook_name):
            names = callback_name_cache.get(hook_name)

            if names is not None:
                return names

            names = tuple(
                original_callback_names(hook_name)
            )

            callback_name_cache[hook_name] = names

            performance["cached_hooks"] += 1

            return names

        plugin_manager.callback_names = cached_callback_names

        #
        # DIRECT CALLBACK CACHE
        #

        plugin_manager._dispatch_cache = {}

        original_add_error = plugin_manager.add_error
        helper_run = Helper.run

        def fast_call_plugin(
            plugin,
            callback_name,
            *args,
            **kwargs,
        ):
            dispatch_cache = plugin_manager._dispatch_cache

            plugin_cache = dispatch_cache.get(id(plugin))

            if plugin_cache is None:
                plugin_cache = {}
                dispatch_cache[id(plugin)] = plugin_cache

            callback = plugin_cache.get(callback_name)

            if callback is None:
                callback = getattr(
                    plugin,
                    callback_name,
                    None,
                )

                plugin_cache[callback_name] = callback

            if callback is None:
                return None

            performance["fast_calls"] += 1

            try:
                result = callback(*args, **kwargs)

                return helper_run(
                    callback_name,
                    result,
                    {
                        "plugin_manager": plugin_manager,
                        "plugin": plugin,
                        "callback": callback_name,
                        "args": args,
                        "kwargs": kwargs,
                    },
                )

            except Exception as exc:
                import traceback

                original_add_error(
                    {
                        "plugin": getattr(
                            plugin,
                            "name",
                            plugin.__class__.__name__,
                        ),

                        "hook": callback_name,
                        "error": str(exc),
                        "traceback": traceback.format_exc(),
                    }
                )

                return None

        plugin_manager.call_plugin = fast_call_plugin

    def on_ui_ready(self, manager, window):
        """
        Reduce Qt repaint overhead.
        """

        original_refresh_ui = window.refresh_ui

        def optimized_refresh_ui(*args, **kwargs):
            widgets = (
                window.bundle_list,
                window.file_list,
                window.detected_list,
                window.folder_list,
            )

            for widget in widgets:
                widget.setUpdatesEnabled(False)
                widget.blockSignals(True)

            try:
                return original_refresh_ui(
                    *args,
                    **kwargs,
                )

            finally:
                for widget in widgets:
                    widget.blockSignals(False)
                    widget.setUpdatesEnabled(True)
                    widget.viewport().update()

        window.refresh_ui = optimized_refresh_ui


Helper.plugin(Plugin)