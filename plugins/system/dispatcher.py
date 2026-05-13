from core.PluginManager import Helper, PluginBase


class Plugin(PluginBase):
    """
    Global dispatcher plugin.

    Converts normal hook execution into structured event payloads
    so patches can act as middleware without modifying Helper core.
    """

    name = "Dispatcher"
    version = "0.0.1"
    author = "Team Stratware"
    description = (
        "Core event routing plugin responsible for "
        "dispatching hooks, runtime callbacks, and "
        "plugin communication across the framework"
    )
    priority = -100

    #
    # INTERNAL
    #

    def event(self, name, manager=None, **data):
        payload = {
            "event": name,
            "manager": manager,
        }

        payload.update(data)

        return payload

    #
    # APP
    #

    def on_app_start(self, app):
        return self.event(
            "on_app_start",
            app=app,
        )

    #
    # CONFIG
    #

    def on_config_loaded(self, manager, data):
        return self.event(
            "on_config_loaded",
            manager,
            data=data,
        )

    def on_config_saving(self, manager, data):
        return self.event(
            "on_config_saving",
            manager,
            data=data,
        )

    #
    # FOLDERS
    #

    def on_folder_added(self, manager, path):
        return self.event(
            "on_folder_added",
            manager,
            path=path,
        )

    def on_folder_removed(self, manager, path):
        return self.event(
            "on_folder_removed",
            manager,
            path=path,
        )

    #
    # SCANNING
    #

    def before_scan(self, manager, initial):
        return self.event(
            "before_scan",
            manager,
            initial=initial,
        )

    def after_scan(self, manager, initial, grouped):
        return self.event(
            "after_scan",
            manager,
            initial=initial,
            grouped=grouped,
        )

    #
    # FILES
    #

    def on_new_file_detected(self, manager, path):
        return self.event(
            "on_new_file_detected",
            manager,
            path=path,
        )

    def on_file_grouped(
        self,
        manager,
        path,
        category,
        bundle_name,
        file_data,
    ):
        return self.event(
            "on_file_grouped",
            manager,
            path=path,
            category=category,
            bundle_name=bundle_name,
            file_data=file_data,
        )

    def on_file_double_click(self, manager, file_data):
        return self.event(
            "on_file_double_click",
            manager,
            file_data=file_data,
        )

    #
    # BUNDLES
    #

    def after_bundle_built(self, manager, category, bundle):
        return self.event(
            "after_bundle_built",
            manager,
            category=category,
            bundle=bundle,
        )

    def on_bundle_selected(self, manager, bundle):
        return self.event(
            "on_bundle_selected",
            manager,
            bundle=bundle,
        )

    def on_bundle_double_click(self, manager, bundle):
        return self.event(
            "on_bundle_double_click",
            manager,
            bundle=bundle,
        )

    #
    # TOGGLING
    #

    def before_toggle_bundle(self, manager, bundle, enabling):
        return self.event(
            "before_toggle_bundle",
            manager,
            bundle=bundle,
            enabling=enabling,
        )

    def before_toggle_file(self, manager, path, enabling):
        return self.event(
            "before_toggle_file",
            manager,
            path=path,
            enabling=enabling,
        )

    def after_toggle_file(self, manager, old_path, new_path, enabling):
        return self.event(
            "after_toggle_file",
            manager,
            old_path=old_path,
            new_path=new_path,
            enabling=enabling,
        )

    def after_toggle_bundle(self, manager, bundle, enabling):
        return self.event(
            "after_toggle_bundle",
            manager,
            bundle=bundle,
            enabling=enabling,
        )

    #
    # UI
    #

    def on_ui_ready(self, manager, window):
        return self.event(
            "on_ui_ready",
            manager,
            window=window,
        )

    def on_ui_refreshed(self, manager, window):
        return self.event(
            "on_ui_refreshed",
            manager,
            window=window,
        )

    #
    # RENDERING
    #

    def format_bundle_row(self, manager, bundle, default_text):
        return self.event(
            "format_bundle_row",
            manager,
            bundle=bundle,
            default_text=default_text,
        )

    def format_file_row(self, manager, file_data, default_text):
        return self.event(
            "format_file_row",
            manager,
            file_data=file_data,
            default_text=default_text,
        )

    def format_status(self, manager, default_text):
        return self.event(
            "format_status",
            manager,
            default_text=default_text,
        )

    #
    # COLORS
    #

    def bundle_color(self, manager, bundle):
        return self.event(
            "bundle_color",
            manager,
            bundle=bundle,
        )

    def file_color(self, manager, file_data):
        return self.event(
            "file_color",
            manager,
            file_data=file_data,
        )


Helper.plugin(Plugin)