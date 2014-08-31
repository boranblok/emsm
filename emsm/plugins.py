#!/usr/bin/python3

# The MIT License (MIT)
# 
# Copyright (c) 2014 Benedikt Schmitt <benedikt@benediktschmitt.de>
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


# Modules
# ------------------------------------------------

# std
import os
import sys
import logging
import importlib.machinery

# local
from .base_plugin import BasePlugin


# Backward compatibility
# ------------------------------------------------

if hasattr(importlib.machinery, "SourceFileLoader"):
    def _import_module(name, path):
        loader = importlib.machinery.SourceFileLoader(name, path)
        return loader.load_module()
else:
    import imp
    _import_module = imp.load_source
    del imp


# Data
# ------------------------------------------------

__all__ = [
    "PluginException",
    "PluginUnavailableError",
    "PluginImplementationError",
    "PluginOutdatedError",
    "PluginManager",
    ]

log = logging.getLogger(__name__)


# Exceptions
# ------------------------------------------------

class PluginException(Exception):
    """
    Base exception for all exceptions in this module.
    """
    pass


class PluginUnavailableError(PluginException):
    """
    Raised if a plugin could not be found.
    """

    def __init__(self, plugin, msg=str()):
        self.plugin = plugin
        self.msg = msg
        return None

    def __str__(self):
        temp = "The plugin '{}' is not available. {}"\
               .format(self.plugin, self.msg)
        return temp


class PluginImplementationError(PluginException):
    """
    Raised if a plugin is not correct implemented.

    For example, when the plugin does not inherit BasePlugin or
    the module does not contain the ``PLUGIN`` variable which
    is the name of the plugin class in the module.
    """

    def __init__(self, plugin, msg):
        self.plugin = plugin
        self.msg = msg
        return None

    def __str__(self):
        temp = "The plugin '{}' is not correct implemented. {}"\
               .format(self.plugin, self.msg)
        return temp

    
class PluginOutdatedError(PluginException):
    """
    Raised if the version of the plugin is not compatible with
    the EMSM version.
    """

    def __init__(self, plugin):
        self.plugin = plugin
        return None

    def __str__(self):
        temp = "The plugin '{}' is outdated.".format(self.plugin)
        return temp


# Classes
# ------------------------------------------------

class PluginManager(object):
    """
    Manages and contains all plugins.

    The prupose of this class is to load and dispatch the plugins.
    
    See also:
        * BasePlugin()
        * hello_dolly.py
    """

    def __init__(self, app):
        """
        """
        self._app = app

        # Maps the module name to the module object.
        self._plugin_modules = dict()

        # Maps the module name to the plugin class.
        self._plugin_types = dict()

        # Maps the module name to the plugin instance.
        self._plugins = dict()
        return None

    def get_module(self, plugin_name):
        """
        Returns the Python module object that contains the plugin with the
        name *plugin_name* or None if there is no plugin with that name.
        """
        return self._plugin_modules.get(plugin_name)
    
    def get_plugin_type(self, plugin_name):
        """
        Returns the plugin class for the plugin with the name *plugin_name* or
        None, if there is no plugin with that name.
        """
        return self._plugin_types.get(plugin_name)
    
    def plugin_is_available(self, plugin_name):
        """
        Returns true, if the plugin with the name *plugin_name* is available.
        """
        return plugin_name in self._plugin_modules

    def get_plugin_names(self):
        """
        Returns the names of all available plugins.
        """
        return list(self._plugin_modules.keys())
    
    def get_plugin(self, plugin_name):
        """
        Returns the instance of the plugin with the name *plugin_name* that is
        currently loaded and used by the EMSM.
        """
        return self._plugins.get(plugin_name)

    def get_all_plugins(self):
        """
        Returns all currently loaded plugin instances.

        See also:
            * get_plugin_names()
            * get_plugin()
        """
        return self._plugins.values()

    def _plugin_is_outdated(self, plugin):
        """
        Returns ``True`` if the *plugin* is outdated and not compatible with
        the current EMSM version.

        See also:
            * Application.VERSION

        Web:
            * http://semver.org
        """        
        app_version = self._app.VERSION.split(".")
        plugin_version = plugin.VERSION.split(".")

        # The version number is invalid.
        if len(plugin_version) < 2:
            return True
        # Only a change in the major version number means a break
        # with the API.
        elif app_version[0] != plugin_version[0]:
            return True
        else:
            return False

    def import_plugin(self, path):
        """
        Loads the plugin which is implemented in the module at *path*.

        Note:
            * The *path* is no longer added to ``sys.path`` (EMSM Vers. >= 3).
              Check if your plugin needs to import from the ``plugins`` folder.

        Parameters:
            * path
                The path of the module, that contains a plugin.
                
        Exceptions:
            * PluginOutdatedError

        See also:
            * _plugin_is_outdated()
        """
        # The module name is the name of the plugin.
        # I assume, that a modulename always ends with '.py'.
        name = os.path.basename(path)
        name = name[:-3]

        # Try to import the module.
        try:
            module = _import_module(name, path)
        except ImportError as error:
            raise PluginUnavailableError(name, error)

        # Check if the module contains a plugin.
        if not hasattr(module, "PLUGIN"):
            msg = "The gloabal 'PLUGIN' variable is not defined."
            raise PluginImplementationError(name, msg)

        if not hasattr(module, module.PLUGIN):
            msg = "The plugin module '{}' does not contain the declared "\
                  "plugin class '{}'".format(name, module.PLUGIN)
            raise PluginImplementationError(name, msg)

        # Get the plugin class.
        plugin_type = getattr(module, module.PLUGIN)

        # The plugin has to be a subclass of BasePlugin.
        if not issubclass(plugin_type, BasePlugin):
            msg = "The plugin '{}' is not a subclass of BasePlugin."\
                  .format(module.PLUGIN)
            raise PluginImplementationError(name, msg)

        # Check if the plugin is tested and compatible with the current
        # EMSM version.
        if self._plugin_is_outdated(plugin_type):
            PluginOutdatedError(name)

        # Save the plugin module and class.
        # A plugin instance is created later, when it is first needed.
        self._plugin_modules[name] = module
        self._plugin_types[name] = plugin_type
        return None

    def import_from_directory(self, directory):
        """
        Imports all Python modules in the *directory*.

        Python modules that contain no plugins or invalid plugins create
        a log entry and are ignored.

        See also:
            * import_plugin()
        """
        def file_is_plugin(path):
            """
            Returns ``True`` if the path probably points to a plugin module.
            """
            filename = os.path.basename(path)
            if os.path.isdir(path):
                return False
            elif filename.startswith("_"):
                return False
            elif not filename.endswith(".py"):
                return False
            elif filename.count(".") != 1:
                return False
            return True

        for filename in os.listdir(directory):
            path = os.path.join(directory, filename)
            if not file_is_plugin(path):
                continue

            try:
                self.import_plugin(path)
            except PluginImplementationError as err:
                print(err)
                log.warning(err)
            except PluginOutdatedError as err:
                log.warning(err)
                print(err)
            except PluginUnavailableError as err:
                log.warning(err)
                print(err)
        return None

    def remove_plugin(self, plugin_name, call_finish=False):
        """
        Unloads the plugin with the name *plugin_name*.

        Parameters:
            * plugin_name
                The name of the plugin that should be removed.
            * call_finish
                If true, the *finish()* method of the plugin is called, before
                it is removed.
        """
        plugin = self._plugins.get(plugin_name, None)

        # Break if there is not plugin with that name.
        if plugin is None:
            return None
        
        if call_finish:
            plugin.finish()

        # Remove the plugin.
        del self._plugins[plugin_name]
        del self._plugin_types[plugin_name]
        del self._plugin_modules[plugin_name]

        # The plugin has been removed.
        log.info("The plugin '{}' has been removed.".format(plugin_name))
        return None

    def uninstall(self, plugin_name):
        """
        Uninstalls the plugin with the name *plugin_name*.

        During uninstallation, ``BasePlugin.uninstall()`` is called and
        then the plugin is unloaded by calling ``remove_plugin()``.

        See also:
            * BasePlugin.uninstall()
            * remove_plugin()
        """
        plugin = self._plugins.get(plugin_name)

        # Break if there is not plugin with the given name.
        if plugin is None:
            return None

        # Uninstall the plugin.
        plugin.uninstall()
        self.unload(plugin_name=plugin_name, call_finish=False)
        return None
    
    def setup(self):
        """
        Imports all plugins from the application's defult plugin directory.

        See also:
            * Pathsystem.plugins()
        """
        plugins_dir = self._app.paths().plugins_dir()
        self.import_from_directory(plugins_dir)
        return None

    def init_plugins(self):
        """
        Creates a plugin instance for each loaded plugin class.

        When you call this method multiple times, only plugins that have
        not been initialised already, will be initialised.
        """
        # Initialise the plugins corresponding to their *INIT_PRIORITY*
        init_queue = self._plugin_types.items()
        init_queue = sorted(init_queue, key=lambda e: e[1].INIT_PRIORITY)
        
        for name, plugin_type in init_queue:
            
            # The plugin has already been initialised.
            if name in self._plugins:
                continue

            # Create a new plugin instance and save it.
            plugin = plugin_type(self._app, name)
            self._plugins[name] = plugin
        return None
    
    def run(self):
        """
        Calls BasePlugin.run() of the plugin that has been selected with the
        command line arguments.

        See also:
            * ArgumentParser.args()
        """
        # Get the name of the selected plugin.
        args = self._app.argparser().args()
        plugin_name = args.plugin

        # Break if no plugin has been selected.
        if plugin_name is None:
            return None

        # Execute the plugin.
        plugin = self._plugins[plugin_name]
        plugin.run(args)
        return None

    def finish(self):
        """
        Calls BasePlugin.finish() for each loaded plugin

        See also:
            * BasePlugin.finish()
        """
        finish_queue = self._plugins.values()
        finish_queue = sorted(finish_queue, key=lambda p: p.FINISH_PRIORITY)
        
        for plugin in finish_queue:
            plugin.finish()
        return None