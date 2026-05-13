import subprocess

from PyQt5.QtWidgets import QMessageBox

from core.PluginManager import Helper, PluginBase


class Plugin(PluginBase):
    """
    Demo subprocess plugin.

    Shows:
    - ui_render pipeline usage
    - toolbar action injection
    - subprocess permission detection
    - safe subprocess execution
    """

    name = "Subprocess Demo"
    version = "1.0.0"
    author = "Team Stratware"
    priority = 150

    def ui_render_hook(
        self,
        manager,
        window,
        slot,
        context,
    ):
        """
        Inject toolbar button.
        """

        if slot != "toolbar":
            return None

        return {
            "type": "action",
            "text": "Open Notepad",
            "callback": lambda: self.open_notepad(window),
        }

    def open_notepad(self, window):
        """
        Launch subprocess safely.
        """

        try:
            subprocess.Popen(
                [
                    "notepad.exe",
                ]
            )

            QMessageBox.information(
                window,
                "Subprocess Demo",
                "Launched notepad.exe",
            )

        except Exception as exc:
            QMessageBox.critical(
                window,
                "Subprocess Demo",
                f"Failed to launch process:\n\n{exc}",
            )


Helper.plugin(Plugin)