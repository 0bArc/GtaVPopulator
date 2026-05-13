import re

from core.PluginManager import Helper, PluginBase


@Helper.patch("format_bundle_row")
def patch_lemonui_name(result, context):
    bundle = context["args"][1]
    default_text = context["args"][2]

    name = bundle.get("name", "")

    if "lemonui" in name.lower():
        return default_text.replace(
            bundle["name"],
            "LemonUI",
        )

    return result

class Plugin(PluginBase):
    name = "Extra Info"
    version = "1.2.0"
    description = "Shows extra metadata information"
    author = "Team Stratware"

    INFO = {
        "heapadjuster": {
            "title": "HeapAdjuster",
            "description": (
                "Increases GTA V memory heap limits to improve "
                "stability with large mod setups."
            ),
            "priority": 10,
        },

        "packfilelimitadjuster": {
            "title": "PackFileLimitAdjuster",
            "description": (
                "Raises the packfile limit so more mods and DLC "
                "archives can load."
            ),
            "priority": 10,
        },

        "ragepluginhook": {
            "title": "RagePluginHook",
            "description": (
                "Framework used primarily by LSPDFR plugins "
                "and advanced GTA V scripting mods."
            ),
            "priority": 1,
        },

        "lemonui": {
            "title": "LemonUI",
            "description": (
                "UI framework library used by many GTA V "
                "trainers and script mods."
            ),
            "priority": 100,
        },
        "scripthookv": {
            "title": "ScriptHookV",
            "description": (
                "Script Hook V is the library that allows to use GTA V script native functions in custom *.asi plugins." 
                "Note that it doesn't work in GTA Online"
            )
        }
    }

    def get_bundle_info(self, manager, bundle):
        bundle_name = str(bundle.get("name", ""))
        lowered = bundle_name.lower()

        print(f"[EXTRA_INFO] Checking bundle: {bundle_name}")

        segments = [
            segment
            for segment in re.split(r"[._\\-]", lowered)
            if segment
        ]

        matches = []

        # Exact segment matches
        for segment in segments:
            if segment in self.INFO:
                info = self.INFO[segment]

                matches.append(
                    (
                        info.get("priority", 0),
                        len(segment),
                        segment,
                        info,
                    )
                )

        # Partial matches
        for key, info in self.INFO.items():
            if key in lowered:
                matches.append(
                    (
                        info.get("priority", 0),
                        len(key),
                        key,
                        info,
                    )
                )

        if not matches:
            print(f"[EXTRA_INFO] No match for: {bundle_name}")
            return None

        # Highest priority first
        # Then longest key
        matches.sort(reverse=True)

        _, _, matched_key, matched_info = matches[0]

        print(f"[EXTRA_INFO] Matched: {matched_key}")

        return {
            "title": matched_info.get("title", bundle_name),
            "description": matched_info.get(
                "description",
                "No description available.",
            ),
        }


Helper.plugin(Plugin)