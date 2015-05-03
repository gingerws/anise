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

##@package anise.features.packages.win32
##Creation of Win32 distribution packages.
##
## Makes the following new functionality available:
## - task for creating windows installers

import os
import shutil

from anise.framework import projects
from anise.framework import features
from anise.framework import results
from anise.framework import base
from anise import utils


HOOK_WINDOWS_PACKAGE_NSIS_ONINIT = "HOOK_WINDOWS_PACKAGE_NSIS_ONINIT"

HOOK_WINDOWS_PACKAGE_NSIS_ONINSTALL = "HOOK_WINDOWS_PACKAGE_NSIS_ONINSTALL"

HOOK_WINDOWS_PACKAGE_NSIS_GLOBAL = "HOOK_WINDOWS_PACKAGE_NSIS_GLOBAL"

class MenuEntry(utils.packaging.WindowsPackageMenuEntry):
    pass


class tasks:

    ## Builds a Win32 installation executable (as .exe file).
    ##@param architecture The target architecture name.
    ##@param menuentries A list of menu entries for creation on target machines.
    @staticmethod
    @utils.logging.log_start_stop("Creating win32 package")
    def win32exepackage(source=None, architecture="all", menuentries=[], projecticon=None, oninitscript="",
                        oninstallscript=""):
        project = projects.currentproject()
        srcfs = results.source_to_filestructure(source)
        _oninitscript = "\n".join([f() for f in projects.currentproject().gethooks(HOOK_WINDOWS_PACKAGE_NSIS_ONINIT)]) \
                        + "\n" + oninitscript
        _oninstallscript = "\n".join([f() for f in projects.currentproject().gethooks(HOOK_WINDOWS_PACKAGE_NSIS_ONINSTALL)]) \
                           + "\n" + oninstallscript
        _globalscript = "\n".join([f() for f in projects.currentproject().gethooks(HOOK_WINDOWS_PACKAGE_NSIS_GLOBAL)])
        return [utils.packaging.buildwindowsinstallerpackage(name=project.name, version=project.getversion(),
                                                             licensefile=project.license.getfilename(),
                                                             menuentries=menuentries, authors=project.authors[0],
                                                             email=project.email, summary=project.summary,
                                                             projecticon=projecticon,
                                                             architecture=architecture, websiteurl=project.getwebsiteurl(),
                                                             rawpkgpath=srcfs.path, projectfsroot=project.projectdir,
                                                             globalscript=_globalscript,
                                                             oninitscript=_oninitscript,
                                                             oninstallscript=_oninstallscript)]

    ## Returns the DLLs needed for Qt deployment on Windows.
    @staticmethod
    def deployqt5dlls(binsource=None, pluginssource=None):
        project = projects.currentproject()
        filesystem = features.loadfeature("filesystem").featuremodule
        if binsource is None:
            binsource = results.Filestructure(project.qt5windows.bindir)
        if pluginssource is None:
            pluginssource = results.Filestructure(project.qt5windows.pluginsdir + "/platforms")
        result = { "/": base.TaskExecution(project.filesystem.tasks.filterbynamepattern,
                                           include=["qt5core.dll", "qt5gui.dll", "qt5concurrent.dll", "qt5webkit.dll",
                                                    "qt5webkitwidgets.dll", "qt5widgets.dll", "qt5xml.dll",
                                                    "qt5opengl.dll", "qt5printsupport.dll", "qt5positioning.dll",
                                                    "qt5sql.dll", "qt5qml.dll", "qt5quick.dll", "qt5webchannel.dll",
                                                    "qt5network.dll", "qt5multimedia.dll", "qt5multimediawidgets.dll",
                                                    "qt5sensors.dll", "icu.*.dll", "libwinpthread.*.dll",
                                                    "libstdc.*.dll", "libgcc.*.dll"],
                                           casesensitive=False, source=binsource),
                   "/platforms": base.TaskExecution(filesystem.tasks.filterbynamepattern, include=["qwindows.dll", ],
                                                    casesensitive=False, source=pluginssource) }
        return results.source_to_filestructure(result)
