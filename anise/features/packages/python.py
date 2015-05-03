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

##@package anise.features.packages.python
##Creation of Python distribution packages.
##
## Makes the following new functionality available:
## - task for creating python wheel packages

from anise.framework import projects
from anise.framework import features
from anise.framework import results
from anise import utils

import anise.features.packages.win32

class WheelApplicationLink(utils.packaging.PythonWheelPackageApplicationLink):
    pass


class tasks:

    ## Builds a python wheel for distribution of Python applications.
    ##@param consolescripts List of wheel entry points for console scripts.
    ##@param guiscripts List of wheel entry points for gui scripts.
    @staticmethod
    @utils.logging.log_start_stop("Creating python wheel")
    def wheelpackage(source=None, applicationlinks=None):
        project = projects.currentproject()
        srcfs = results.source_to_filestructure(source)
        return [utils.packaging.buildpythonwheelpackage(name=project.name, version=project.getversion(),
                                                        homepage=project.getwebsiteurl(),
                                                        description=project.summary,
                                                        long_description=project.longdescription,
                                                        licensename=project.license.namepythonsetuputils,
                                                        maturity=project.maturity,
                                                        authors=project.authors, email=project.email,
                                                        keywords=project.keywords,
                                                        fsroot=srcfs.path,
                                                        applicationlinks=applicationlinks)]


@features.hook(anise.features.packages.win32.HOOK_WINDOWS_PACKAGE_NSIS_GLOBAL)
def _nsis_get_global():
    return """
        !macro RequirePython Version
            Var /Global ANISERV
            Var /Global PYPATH
            StrCpy $PYPATH ""
            StrCpy $ANISERV 1
            StrCpy $0 0
            aniseloop:
                EnumRegKey $1 HKLM "Software\\Python\\PythonCore" $0
                StrCmp $1 "" anisedone
                IntOp $0 $0 + 1
                ${StrLoc} $3 "$1." "${Version}." ">"
                ${If} $3 == '0'
                    ReadRegStr $2 HKLM "Software\\Python\\PythonCore\\$1\\InstallPath" ""
                    StrCpy $PYPATH $2
                ${EndIf}
                Goto aniseloop
            anisedone:
            ExecWait '$PYPATH\\python -V' $ANISERV
            ${If} $ANISERV != '0'
                MessageBox MB_OK "Ginger needs an 'x86' variant of 'Python${Version}' for running. Please download the latest at https://www.python.org/downloads/windows/ and install it."
                Quit
            ${EndIf}
        !macroend
    """
