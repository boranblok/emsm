#!/usr/bin/python3
"""
About
-----

Extends the EMSM by the ability to call a custom shell script with parameters concerning the world.

Configuration
-------------

.. code-block:: ini

    [shellscript]
    script_path = /home/ben/test.sh {0} {1}
    suspend_world_io = true

**script_path**

    The shell script to execute. First argument is the world directory second argument is world name

**suspend_world_io**

    Wether or not to suspend world i/o before executing the script.
    When enabled the world will do save-off, save-all before script execution and save-on, save-all afterwards

Arguments
---------
.. option:: --path, -p

    Path to the shell script that is to be executed. 
    Overwrites the configuration section.

.. option:: --suspendio, -s

    When specified the world will do save-off, save-all before script execution and save-on, save-all afterwards
    Overwrites the configuration section.

Usage
-----

.. code-block:: bash

    # Will call the script once for each world:
    minecraft -W shellscript
   
    # Calls the script ~/dummy.sh for the vanilla world with suspending I/O regdardless of setting in the configuration:
    minecraft -w vanilla shellscript --path ~/dummy.sh --suspendio
"""


# Modules
# ------------------------------------------------
import os
import shutil


# local
import world_wrapper
import configuration
from base_plugin import BasePlugin
from app_lib import pprinttable
from app_lib import userinput


# Data
# ------------------------------------------------
PLUGIN = "ShellScript"
# The PLUGIN_VERSION is not related to the EMSM version number.
PLUGIN_VERSION = "1.0.0"

# Classes
# ------------------------------------------------
class ShellScript(BasePlugin):
    
    version = "2.0.0"

    def __init__(self, application, name):
        """
        """
        BasePlugin.__init__(self, application, name)
        self._setup_conf()
        self._setup_argparser()
        return None

    def _setup_conf(self):
        """
        Sets the configuration up.
        """
        # Get the configuration dictionary for this plugin.
        conf = self.conf()        
        self._script_path = conf.get("script_path")
        self._suspend_world_io = conf.getboolean("suspend_world_io", True)

        conf.clear()
        conf["script_path"] = self._script_path
        conf["suspend_world_io"] = self._suspend_world_io
        return None

    def _setup_argparser(self):
        """
        Sets the argument parser up.
        """
        # Get the plugin's argument parser.
        parser = self.argparser()

        parser.add_argument("--path", "-p",
            action = "store",
            dest = "path",
            type = str,
            default = "",
            metavar = "PATH",
            help = "The path to the script file that has to be executed.")

        parser.add_argument("--suspendio", "-s",
            action = "count",
            dest = "suspendio",
            help = "If specified I/O of the world will be suspended before the script executes and resumed afterwards.")
        return None

    def run(self, args):
        """
        """

        scriptpath = self._script_path
        if args.path:
            scriptpath = args.path

        suspendio = self._suspend_world_io
        if args.suspendio:
            suspendio = True

        worlds = self.app().worlds().get_selected()
        for world in worlds:
            if suspendio:
                try:            
                    if world.is_online():                
                        world.send_command("save-off")
                        # We use verbose send, to wait until the world has been
                        # saved.
                        world.send_command_get_output("save-all", timeout=10)

                    # Copy the world data to *backup_dir*.
                    self.executescript(scriptpath, world)
                finally:
                    if world.is_online():
                        world.send_command("save-on")
                        world.send_command("save-all")
            else:
                self.executescript(scriptpath, world)
        return None

    def executescript(self, scriptpath, world):
        """
        """
        print("script {0} for world {1} would be executed".format(scriptpath, world.name()))