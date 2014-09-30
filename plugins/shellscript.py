#!/usr/bin/python3

# The MIT License (MIT)
# 
# Copyright (c) 2014 Ben Blok <ben.blok@gmail.com>
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

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

    The shell script to execute.
    Passed arguments are in order:
        0. World name
        1. Path to world files

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
        # for 3.0.0 this is self.conf()  
        conf = self.conf
        self._script_path = conf.get("script_path", "")
        print("conf.get:script_path {}".format(self._script_path))
        self._suspend_world_io = conf.getboolean("suspend_world_io", True)

        # maybe required in 3.0.0 : conf.clear()
        conf["script_path"] = self._script_path
        conf["suspend_world_io"] = str(self._suspend_world_io)
        return None

    def _setup_argparser(self):
        """
        Sets the argument parser up.
        """
        # for 3.0.0 this is self.argparser()
        parser = self.argparser

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

        if not scriptpath:
            print("conf:script_path is empty and --script param is as well.")
            raise ValueError("conf:script_path is empty and --script param is as well.")

        suspendio = self._suspend_world_io
        if args.suspendio:
            suspendio = True
        
        # in 3.0.0 this is self.app().worlds().get_selected()
        worlds = self.app.worlds.get_selected()
        for world in worlds:
            if suspendio:
                try:
                    print("World {0} I/O will be halted".format(world.name))
                    if world.is_online():                
                        world.send_command("save-off")
                        # We use verbose send, to wait until the world has been
                        # saved.
                        world.send_command_get_output("save-all", timeout=30)

                    self.executescript(scriptpath, world)
                finally:
                    print("World {0} I/O will be resumed".format(world.name))
                    if world.is_online():
                        world.send_command("save-on")
                        world.send_command("save-all")
            else:
                self.executescript(scriptpath, world)
        return None

    def executescript(self, scriptpath, world):
        """
        """

        # in 3.0.0 this is world.name()
        print("script {0} for world {1} will be executed".format(scriptpath, world.name))
        os.spawnl(os.P_WAIT, scriptpath, scriptpath, world.name, world.directory)