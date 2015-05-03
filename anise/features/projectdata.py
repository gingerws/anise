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

##@package anise.features.projectdata
## Often used data structures and some smaller services.
##
## Makes the following new functionality available:
## - automatically beautifies `project.longdescription`
## - determining the specified project maturity as string
## - enumerations for some project data

import os
import shutil

from anise.framework import projects
from anise.framework import features
from anise import utils
from anise.framework import results


## This class helps describing the project state.
class Maturity:
    Planning = 'Development Status :: 1 - Planning'
    PreAlpha = 'Development Status :: 2 - Pre-Alpha'
    Alpha = 'Development Status :: 3 - Alpha'
    Beta = 'Development Status :: 4 - Beta'
    ProductionStable = 'Development Status :: 5 - Production/Stable'
    Mature = 'Development Status :: 6 - Mature'
    Inactive = 'Development Status :: 7 - Inactive'


@features.hook(features.HOOK_BEFORE_DEFINITION)
def _initproject():
    # set some default
    projects.currentproject().email = None
    projects.currentproject().keywords = ""
    projects.currentproject().getprojectstatusdescription = tasks.getprojectstatusdescription


@features.hook(features.HOOK_BEFORE_EXECUTION)
def _beautify_longdescription():
    project = projects.currentproject()
    def hascommonprefixlength(l, lst):
        if len(lst) == 0:
            return False
        pre = lst[0][0:l]
        if len(pre) < l:
            return False
        if pre.strip() != "":
            return False
        return 0 == len([x for x in lst[1:] if not x.startswith(pre)])
    _ls = project.longdescription.split("\n")
    ls = _ls[1:-1]
    commonprefixlength = 0
    while hascommonprefixlength(commonprefixlength + 1, ls):
        commonprefixlength += 1
    for i in range(1, len(_ls) - 1):
        _ls[i] = _ls[i][commonprefixlength:]
    if _ls[-1][0:commonprefixlength].strip() == "":
        _ls[-1] = _ls[-1][commonprefixlength:]
    project.longdescription = "\n".join([l.rstrip() for l in _ls])


class tasks:

    ## Returns a short plaintext describing the specified project maturity (`project.maturity`).
    ##@param short If The output shall be a very reduced one.
    @staticmethod
    def getprojectstatusdescription(short=False):
        project = projects.currentproject()
        if hasattr(project, "maturity"):
            if project.maturity == Maturity.Planning:
                w = "planning"
            if project.maturity == Maturity.PreAlpha:
                w = "pre-alpha"
            if project.maturity == Maturity.Alpha:
                w = "alpha"
            if project.maturity == Maturity.Beta:
                w = "beta"
            if project.maturity == Maturity.ProductionStable:
                w = "production-stable"
            if project.maturity == Maturity.Mature:
                w = "mature"
            if project.maturity == Maturity.Inactive:
                w = "inactive"
            if short:
                return w
            else:
                return "In this version, the state of {name} is considered as {w}.".format(name=project.name, w=w)
        else:
            return ""
