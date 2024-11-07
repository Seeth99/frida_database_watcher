from objection.utils.plugin import Plugin
from objection.state.connection import state_connection
from .modules.helpers import AppData, RPCException
from .modules.gui import Gui
import os


class Watcher(Plugin):
    def __init__(self, ns):
        """
        Creates a new instance of the plugin

        :param ns:
        """

        # plugin sources are specified, so when the plugin is loaded it will not
        # try and discover an index.js next to this file.
        # self.script_src = s

        # as script_src is specified, a path is not necessary. this is simply an
        # example of an alternate method to load a Frida script
        # self.script_path = os.path.join(os.path.dirname(__file__), "script.js")

        implementation = {
            "meta": "Plugin to help you monitor selected database(s)",
            "commands": {
                "run": {
                    "meta": "Run the plugin",
                    "exec": self.run,
                }
            },
        }

        super().__init__(__file__, ns, implementation)

        self.inject()

    def run(self, args: list):
        try:
            path_dict = state_connection.get_api().env_ios_paths()
            # root_path = os.path.dirname(
            #     path_dict["DocumentDirectory"])
            root_path = path_dict["DocumentDirectory"]
        except RPCException:
            path_dict = state_connection.get_api().env_android_paths()
            root_path = os.path.dirname(
                path_dict["cacheDirectory"])

        app_data = AppData(api=state_connection.get_api(),
                           application_root_path=root_path)

        Gui(app_data).start_gui()


# Needed for Objection Plugin
namespace = "dbwatcher"
plugin = Watcher
