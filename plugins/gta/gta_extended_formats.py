from core.PluginManager import Helper, PluginBase


class Plugin(PluginBase):
    name = "GTA Extended Formats"
    version = "0.0.1"
    description = "File extension extender to show more files"
    author = "Team Stratware"

    supported_extensions = {
        ".asi",
        ".dll",
        ".lua",
        ".rpf",
        ".ini",
        ".meta",
        ".xml",
        ".ymap",
        ".ytyp",
        ".ytd",
        ".yft",
        ".pdb",
    }

    categories = [
        "Archives",
        "Maps",
        "Metadata",
        "Models",
        "Textures",
        "Debug",
    ]

    def detect_category(self, manager, path):
        extension = self._actual_extension(path)

        if extension == ".lua":
            return "Scripts"

        if extension == ".rpf":
            return "Archives"

        if extension in {".ymap", ".ytyp"}:
            return "Maps"

        if extension == ".meta":
            return "Metadata"

        # XML stays in BaseGame
        if extension == ".xml":
            lower = str(path).replace("/", "\\").lower()

            if "\\scripts\\" in lower:
                return "Scripts"

            if "\\plugins\\" in lower:
                return "Plugins"

            if "\\lspdfr\\" in lower:
                return "LSPDFR"

            if "\\stream\\" in lower:
                return "Maps"

            return "BaseGame"

        if extension == ".ytd":
            return "Textures"

        if extension == ".yft":
            return "Models"

        if extension == ".pdb":
            return "Debug"

        return None

    def get_bundle_name(self, manager, path, actual_path, category):
        extension = actual_path.suffix.lower()

        if extension in {
            ".rpf",
            ".ymap",
            ".ytyp",
            ".ytd",
            ".yft",
        }:
            return actual_path.stem

        if extension in {".meta", ".lua"} and path.parent.name:
            return path.parent.name

        if extension == ".xml":
            stem = actual_path.stem

            # LemonUI.RagePluginHook.xml
            # -> LemonUI.RagePluginHook
            if "." in stem:
                return stem

            if path.parent.name:
                return path.parent.name

        if extension == ".pdb":
            return actual_path.stem

        return None

    def format_file_row(self, manager, file_data, default_text):
        path = str(file_data.get("path", "")).lower()

        if path.endswith(".xml"):
            return {
                "text": f"[XML] {default_text}",
                "fg": "#8ecfff",
            }

        if path.endswith(".meta"):
            return {
                "text": f"[META] {default_text}",
                "fg": "#ffd27f",
            }

        if path.endswith(".pdb"):
            return {
                "text": f"[PDB] {default_text}",
                "fg": "#ff9b9b",
            }

        return None

    def _actual_extension(self, path):
        if path.suffix == ".disabled":
            return path.with_suffix("").suffix.lower()

        return path.suffix.lower()


Helper.plugin(Plugin)