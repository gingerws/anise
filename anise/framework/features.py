# Copyright (C) 2014-2015, Josef Hahn
#
# This file is part of anise.
#
# anise is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# anise is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with anise.  If not, see <http://www.gnu.org/licenses/>.

##@package anise.framework.features
##anise Features

import importlib
import importlib.machinery
import os
from anise.utils import basic
from anise.utils import logging


HOOK_BEFORE_DEFINITION = "BEFORE_DEFINITION"
HOOK_BEFORE_EXECUTION = "BEFORE_EXECUTION"


# noinspection PyPep8Naming
class internals:

    @staticmethod
    def injectdefaultstoproject(project):
        for feature in _features:
            fname = feature.name if (not "." in feature.name) else feature.name[feature.name.rindex(".")+1:]
            setattr(basic.createobjectstructure(project, feature.name)[1], fname, feature.featuremodule)

    @staticmethod
    def injecthookstoproject(project):
        for feature in _features:
            for hook in feature.hooks:
                project.addhook(hook.eventname, hook.function, None, hook.provides, hook.requires, hook.prepares)

    @staticmethod
    def loadfeatures(featurespath, name=""):
        l = [(featurespath, name)]
        ll = []
        while len(l) > 0:
            xpath, xname = l.pop()
            _featuresources.append((xpath, xname))
            if os.path.isdir(xpath):
                for f in sorted(os.listdir(xpath)):
                    nname = xname
                    if nname != "":
                        nname += "."
                    nname += f
                    if f.startswith("__"):
                        continue
                    if nname.endswith(".py"):
                        nname=nname[:-3]
                    l.append((xpath+"/"+f, nname))
            elif os.path.isfile(xpath):
                ll.append(xname)
        for xxname in ll:
            loadfeature(xxname)


    @staticmethod
    def resetfeatures():
        global _features
        global _featuresources
        logging.logdebug("Resetting features.")
        _features = []
        _featuresources = []


## An hook handler bound to some hook.
class Hook:

    ##@param eventname The hook symbol.
    ##@param function The handler function.
    ##@param provides A space-separated list of symbol names this hook participates to provide (dependency provider).
    ##@param requires A space-separated list of symbol names this hook requires to be executed before.
    ##@param prepares A space-separated list of symbol names this hook must prepend.
    def __init__(self, eventname, function, provides, requires, prepares):
        self.eventname = eventname
        self.function = function
        self.provides = provides
        self.requires = requires
        self.prepares = prepares
        if "PRE" in provides:
            self.prepares.append("DEFAULT")
        elif "POST" in provides:
            self.requires.append("DEFAULT")
        elif not "DEFAULT" in provides:
            self.provides.append("DEFAULT")


## A featue is some encapsuled anise functionality.
class Feature:

    ##@param name The optional name of the feature.
    ##@param hooks All hook handlers this feature registers.
    def __init__(self, name, hooks, featuremodule):
        self.name = name
        self.hooks = list(hooks)
        self.featuremodule = featuremodule


_features = []

_featuresources = []

## Load an anise.framework.features.Feature by name from the predefined sources.
def loadfeature(name):
    global _hooks
    for f in _features:
        if f.name == name:
            return f
    frompath = None
    for srcfile, srcname in _featuresources:
        if srcname==name:
            frompath = srcfile
            break
    if not frompath:
        raise Exception("unable to load feature '" + name + "'.")
    logging.logdebug("Load feature from path '{0}' to name '{1}'.".format(frompath, name))
    _hooks.append([])
    try:
        loader = importlib.machinery.SourceFileLoader(name, frompath)
        m = loader.load_module()
        for hook in _hooks[-1]:
            if not name in hook.provides:
                hook.provides.append(name)
        _feature = Feature(name, _hooks[-1], m)
    finally:
        _hooks.pop(len(_hooks)-1)
    _features.append(_feature)
    _features.sort(key=lambda x: x.name)
    return _feature

_hooks = []


## Used by a feature module to register a hook (mostly used as decorator).
def hook(name, *, provides=None, requires=None, prepares=None):
    def _realdecorator(func):
        _hooks[-1].append(Hook(name, func, provides or [], requires or [], prepares or []))
        return func
    return _realdecorator


