import subprocess

from pathlib import Path

from core.PluginManager import Helper, PluginBase


@Helper.patch("on_file_double_click")
def patch_open_location(result, context):
    if not isinstance(result, dict):
        return result

    file_data = result.get("file_data")

    if not file_data:
        return result

    path = Path(file_data["path"])

    if path.exists():
        subprocess.Popen(
            [
                "explorer",
                "/select,",
                str(path),
            ]
        )

    return result


class Plugin(PluginBase):
    name = "File Location Support"
    version = "1.0.0"
    author = "Team Stratware"
    description = (
        "Adds Explorer integration for opening and "
        "highlighting files from debugger events."
    )
    priority = 50


Helper.plugin(Plugin)