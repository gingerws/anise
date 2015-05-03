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

##@package anise.features.build.qmake
## Compiling binaries with qmake.
##
## Makes the following new functionality available:
## - task for compiling a binary with qmake

import os
import shutil

from anise import utils
from anise.utils import logging
from anise.utils import exceptions
from anise.framework import results
from anise.framework import features
from anise.framework import projects


class QtConfiguration:

    def __init__(self, qtdir, makecmd="make", qmakecmd="bin/qmake"):
        self.qtdir = qtdir
        self.bindir = qtdir + "/bin"
        self.pluginsdir = qtdir + "/plugins"
        self.makecmd = makecmd
        self.qmakecmd = qtdir + "/" + qmakecmd


def basedependencies():
    dependencies = features.loadfeature("dependencies").featuremodule
    return [dependencies.Dependency(dependencies.Type.Required, debian=["libqt5concurrent5"]),
            dependencies.Dependency(dependencies.Type.Required, debian=["libqt5core5a"]),
            dependencies.Dependency(dependencies.Type.Required, debian=["libqt5declarative5"]),
            dependencies.Dependency(dependencies.Type.Required, debian=["libqt5gui5"]),
            dependencies.Dependency(dependencies.Type.Required, debian=["libqt5help5"]),
            dependencies.Dependency(dependencies.Type.Required, debian=["libqt5network5"]),
            dependencies.Dependency(dependencies.Type.Required, debian=["libqt5printsupport5"]),
            dependencies.Dependency(dependencies.Type.Required, debian=["libqt5qml5"]),
            dependencies.Dependency(dependencies.Type.Required, debian=["libqt5quick5"]),
            dependencies.Dependency(dependencies.Type.Required, debian=["libqt5script5"]),
            dependencies.Dependency(dependencies.Type.Required, debian=["libqt5sql5"]),
            dependencies.Dependency(dependencies.Type.Required, debian=["libqt5sql5-sqlite"]),
            dependencies.Dependency(dependencies.Type.Required, debian=["libqt5svg5"]),
            dependencies.Dependency(dependencies.Type.Required, debian=["libqt5webkit5"]),
            dependencies.Dependency(dependencies.Type.Required, debian=["libqt5widgets5"]),
            dependencies.Dependency(dependencies.Type.Required, debian=["libqt5xml5"])]



class tasks:

    ## Builds a binary with qmake.
    ##@param qmakeproject The qmake project file path relative to `source`s root.
    ##@param targetname The name of the make target for creating.
    ##@param qt The qmake.QtConfiguration to use.
    @staticmethod
    @logging.log_start_stop("Building a binary via qmake")
    def build(qmakeproject, qt, targetname=None, targetfile=None, source=None, qmakeoptions=[]):
        srcfs = results.source_to_filestructure(source)
        targetdir = results.TempDir()
        with results.TempDir() as tempdir:
            with utils.basic.ChDir(tempdir.path):
                r, o = utils.basic.call(*([qt.qmakecmd, "-makefile"] + qmakeoptions + [srcfs.path + "/" + qmakeproject]))
                if r != 0:
                    raise exceptions.ProcessExecutionFailedError("unable to run qmake: "+o)
                logging.logdebug(o)
                makecall = [qt.makecmd, "-j6"]
                if targetname:
                    makecall.append(targetname)
                r, o = utils.basic.call(*makecall)
                if r != 0:
                    raise exceptions.ProcessExecutionFailedError("unable to run make: "+o)
                if targetfile is None:
                    targetfile = targetname
                result = results.Filestructure(targetdir.path + "/" + os.path.basename(targetfile))
                if os.path.isdir(targetfile):
                    results.Filestructure(targetfile).dl(to=result.path)
                else:
                    shutil.copy2(targetfile, targetdir.path)
        return result
