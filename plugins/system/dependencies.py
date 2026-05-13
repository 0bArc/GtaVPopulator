"""
Dependency Warning Plugin
=========================

Purpose:
Detect common GTA V mod dependency problems before the user
launches the game.

This plugin helps identify missing loaders, broken requirements,
or incomplete installs during scan time.

What this plugin does:
1) Detects missing ScriptHookV
2) Detects missing ScriptHookVDotNet
3) Detects missing RagePluginHook
4) Detects missing OpenIV.asi
5) Warns about disabled dependencies
6) Extends UI status text with dependency warnings
7) Adds bundle-level warning formatting
"""

from core.PluginManager import Helper, PluginBase


class Plugin(PluginBase):
    name = "Dependency Warning System"
    version = "0.0.1"
    priority = 180

    REQUIRED_DEPENDENCIES = {
        "Scripts": [
            "ScriptHookV",
            "ScriptHookVDotNet",
        ],
        "LSPDFR": [
            "RagePluginHook",
        ],
        "Archives": [
            "OpenIV",
        ],
    }

    def ensure_state(self, manager):
        manager.context.setdefault(
            "dependency_warnings",
            {
                "installed": set(),
                "disabled": set(),
                "missing": [],
            },
        )

    def on_app_start_hook(self, manager):
        """
        Normal plugin lifecycle entrypoint.
        """
        self.ensure_state(manager)

    def before_scan_hook(self, manager, initial):
        """
        Reset dependency state before scan.
        """
        self.ensure_state(manager)

        state = manager.context["dependency_warnings"]

        state["installed"] = set()
        state["disabled"] = set()
        state["missing"] = []

    def on_file_grouped_hook(
        self,
        manager,
        path,
        category,
        bundle_name,
        file_data,
    ):
        """
        Track installed and disabled dependency bundles.
        """
        self.ensure_state(manager)

        state = manager.context["dependency_warnings"]

        normalized = bundle_name.lower()

        aliases = manager.plugin_manager.aliases()

        normalized = aliases.get(normalized, bundle_name)

        if not file_data.get("active", True):
            state["disabled"].add(normalized)
        else:
            state["installed"].add(normalized)

    def after_scan_hook(self, manager, initial, grouped):
        """
        Detect missing dependencies after scan completes.
        """
        self.ensure_state(manager)

        state = manager.context["dependency_warnings"]

        installed = state["installed"]
        disabled = state["disabled"]

        for category, dependencies in self.REQUIRED_DEPENDENCIES.items():
            for dependency in dependencies:

                if dependency not in installed:
                    state["missing"].append(
                        f"{category} requires {dependency}"
                    )

                elif dependency in disabled:
                    state["missing"].append(
                        f"{dependency} is currently disabled"
                    )

    def format_status_hook(self, manager, default_text):
        """
        Add warning count to status bar.
        """

        warnings = (
            manager.context
            .get("dependency_warnings", {})
            .get("missing", [])
        )

        if not warnings:
            return f"{default_text} | dependencies OK"

        return (
            f"{default_text} | "
            f"dependency warnings: {len(warnings)}"
        )

    def format_bundle_row_hook(
        self,
        manager,
        bundle,
        default_text,
    ):
        """
        Highlight bundles with dependency relevance.
        """

        bundle_name = bundle.get("name", "")

        for dependencies in self.REQUIRED_DEPENDENCIES.values():
            for dependency in dependencies:

                if dependency.lower() in bundle_name.lower():
                    return f"[CORE] {default_text}"

        return None

    def on_ui_ready_hook(self, manager, window):
        """
        Print dependency warnings into console for debugging.
        """

        warnings = (
            manager.context
            .get("dependency_warnings", {})
            .get("missing", [])
        )

        for warning in warnings:
            print(f"[DEPENDENCY WARNING] {warning}")


Helper.plugin(Plugin)
