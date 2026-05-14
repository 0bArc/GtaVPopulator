import os
from pathlib import Path

from core.PluginManager import Helper, PluginBase
from core.plugin_permissions import analyze_python_plugin_source


class Plugin(PluginBase):
    name = "Bootstrap Pipelines"
    version = "0.1.0"
    priority = -200
    description = "Runs named bootstrap pipelines (permission scan, etc.)."

    def bootstrap_pipeline_permission_hook(self, manager, state):
        if state is None:
            state = {}

        reports = state.setdefault("reports", [])
        stage = state.get("stage", "")

        if os.environ.get("GTA_POPULATOR_SCAN_PLUGINS_ON_LOAD") != "1":
            manager.context["permission_pipeline_last"] = dict(state)
            return state

        if stage == "bootstrap":
            for path in manager.bootstrap_files():
                reports.append(analyze_python_plugin_source(path))

        elif stage == "after_load":
            seen = set()
            for plugin in manager.plugins:
                path_str = getattr(plugin, "__plugin_file__", None)
                if not path_str:
                    continue
                key = str(Path(path_str).resolve())
                if key in seen:
                    continue
                seen.add(key)
                reports.append(analyze_python_plugin_source(Path(path_str)))

        manager.context["permission_pipeline_last"] = dict(state)
        return state


Helper.plugin(Plugin)
