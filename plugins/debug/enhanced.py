from core.PluginManager import Helper, PluginBase

isEnabled = False

class Plugin(PluginBase):
    name = "UI Enhanced"
    version = "0.0.1"
    author = "Team Stratware"
    description = "Enhanced UI rendering and tracking"
    priority = 220

    def ensure_state(self, manager):
        manager.context.setdefault(
            "ui_enhanced",
            {
                "bundles": 0,
                "files": 0,
                "groups": {},
            },
        )

    def on_app_start_hook(self, manager):
        self.ensure_state(manager)

    def before_scan_hook(self, manager, initial):
        self.ensure_state(manager)

        state = manager.context["ui_enhanced"]

        state["bundles"] = 0
        state["files"] = 0
        state["groups"] = {}

    def after_bundle_built_hook(self, manager, category, bundle):
        self.ensure_state(manager)

        state = manager.context["ui_enhanced"]

        group = self.bundle_group(bundle["name"])

        state["groups"][bundle["name"]] = group
        state["bundles"] += 1

    def format_bundle_row_hook(self, manager, bundle, default_text):
        group = self.bundle_group(bundle["name"])

        tag = group.upper()

        return f"[{tag}] {default_text}"

    def format_file_row_hook(self, manager, file_data, default_text):
        self.ensure_state(manager)

        state = manager.context["ui_enhanced"]
        state["files"] += 1

        path = str(file_data.get("path", "")).lower()

        if path.endswith(".asi"):
            return f"[ASI] {default_text}"

        if path.endswith(".dll"):
            return f"[DLL] {default_text}"

        if path.endswith(".ini"):
            return f"[CFG] {default_text}"

        if path.endswith(".xml"):
            return f"[XML] {default_text}"

        if path.endswith(".meta"):
            return f"[META] {default_text}"

        if path.endswith(".lua"):
            return f"[LUA] {default_text}"

        if path.endswith(".ymap"):
            return f"[YMAP] {default_text}"

        if path.endswith(".ytyp"):
            return f"[YTYP] {default_text}"

        if path.endswith(".pdb"):
            return f"[DEBUG] {default_text}"

        return default_text

    def format_status_hook(self, manager, default_text):
        self.ensure_state(manager)

        state = manager.context["ui_enhanced"]

        return (
            f"{default_text} | "
            f"bundles:{state['bundles']} "
            f"files:{state['files']}"
        )

    def bundle_color_hook(self, manager, bundle):
        group = self.bundle_group(bundle["name"])

        colors = {
            "core": "#ff9090",
            "performance": "#ffd479",
            "graphics": "#8ed0ff",
            "script": "#a8ffbe",
            "map": "#7fe8ff",
            "default": "#f2f2f2",
        }

        return {
            "fg": colors.get(group, "#f2f2f2"),
        }

    def bundle_group(self, name):
        lowered = name.lower()

        if any(
            x in lowered
            for x in (
                "scripthook",
                "ragepluginhook",
                "openiv",
            )
        ):
            return "core"

        if any(
            x in lowered
            for x in (
                "heap",
                "limit",
                "adjuster",
                "optimizer",
            )
        ):
            return "performance"

        if any(
            x in lowered
            for x in (
                "reshade",
                "visual",
                "graphic",
                "shader",
                "texture",
                "nvpmapi",
                "slimdx"
            )
        ):
            return "graphics"

        if any(
            x in lowered
            for x in (
                "script",
                "trainer",
                "lua",
                "menu",
            )
        ):
            return "script"

        if any(
            x in lowered
            for x in (
                "ymap",
                "ytyp",
                "map",
                "mlo",
            )
        ):
            return "map"

        return "default"
    

if isEnabled:
    Helper.plugin(Plugin)
    