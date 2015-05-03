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

##@package anise.features.datainjections
## Helps injecting some kinds of data at anise runtime into some file structures, in order to make it available
## to other build processes (Makefiles, ...) or to the project's runtime.
##
## Makes the following new functionality available:
## - provides a method for adding a data injection
## - getting pieces of project metadata prepared from an injection
## - task for injecting some project metadata to a python source file

import hashlib
import os
import shutil
from anise.framework import projects
from anise.framework import features
from anise.framework import results
from anise import utils
import anise.framework.projectinformations


name = "datainjections"


## Sync if not marked as `omitsyncvcs`.
def _sync():
    project = projects.currentproject()
    if not getattr(project, "omitsyncvcs", False):
        project.syncversioncontrolsystem(commitmessage="automated commit for data injections")
    return True


class _Pool:

    ## Add a data injection.
    ##@param method The implementation for the injection.
    ##@param outfile Path to the target file for the injections (relative to anise project root path).
    ##@param propnames List of entry names you want to inject (beyond the few default ones).
    ##@param do_in_source If the source itself should be updated as well (instead of only the on-the-fly copies for packages).
    ##@param params Additional parameters for calling the injection implementation.
    def add(self, method, outfile, propnames=None, do_in_source=False, **params):
        project = projects.currentproject()
        while outfile.startswith("/"):
            outfile = outfile[1:]
        f = lambda x: method(outfile=x+outfile, data=project.getessentials(propnames), **params)
        if do_in_source:
            project.addhook(features.loadfeature("releasing").featuremodule.HOOK_RELEASE,
                            lambda : _sync() and f(""), provides=["PRE", "datainjections"])
        else:
            project.addhook(features.loadfeature("packages").featuremodule.HOOK_ENRICHRAWPACKAGE,
                            lambda destdir: f(destdir+"/"))


@features.hook(features.HOOK_BEFORE_DEFINITION, provides=["datainjections"])
def _initproject():
    projects.currentproject().datainjections.pool = _Pool()
    projects.currentproject().getessentials = tasks.getessentials


class tasks:

    ## Retuns a list of name/value tuples taken from the project object, in order to provide some project metadata like
    ## the version number.
    ##@param propnames List of entry names you want to fetch (beyond the few default ones).
    @staticmethod
    def getessentials(propnames=None):
        project = projects.currentproject()
        data = []
        data.append(("version", project.getversion()))
        if hasattr(project, "getwebsiteurl"):
            data.append(("homepage", project.getwebsiteurl()))
        for propname in propnames or []:
            propvalue = getattr(project, propname, None)
            data.append((propname, propvalue))
        return data


    ## Injects some project data into a Python file, so it is available at program's runtime.
    ##@param outfile path to the target file, either absolute or relative to the project's root.
    ##@param asclass if the output shall be wrapped into a class definition, give a class name here.
    def inject_python(outfile=None, data=None, asclass=None):
        result = """
# This file is automatically created by 'anise' in order to make some
# information available at runtime. Do not change stuff here.
#   Information about anise:
#   {anisehomepage}
""".format(anisehomepage=anise.framework.projectinformations.homepage)[1:]
        if asclass:
            result += "class " + asclass + ":\n"
            indent = "    "
        else:
            result += ""
            indent = ""
        # determine destination
        if outfile:
            if outfile.startswith("/"):
                fulloutfile = outfile
            else:
                fulloutfile = projects.currentproject().projectdir + "/" + outfile
        else:
            tempdir = results.TempDir()
            fulloutfile = tempdir.path + "/out.py"
        # write them to outfile
        for propname, propvalue in data or []:
            propvalue = repr(propvalue)
            result += "{indent}{propname} = {propvalue}\n".format(**locals())
        utils.basic.writetofile(fulloutfile, result)
        return results.Filestructure(fulloutfile)


    def inject_c(outfile=None, data=None):
        result = """
// This file is automatically created by 'anise' in order to make some
// information available at runtime. Do not change stuff here.
//   Information about anise:
//   {anisehomepage}
#ifndef ANISE_PROJECT_INFORMATION_H
#define ANISE_PROJECT_INFORMATION_H
""".format(anisehomepage=anise.framework.projectinformations.homepage)[1:]
        # determine destination
        if outfile:
            if outfile.startswith("/"):
                fulloutfile = outfile
            else:
                fulloutfile = projects.currentproject().projectdir + "/" + outfile
        else:
            tempdir = results.TempDir()
            fulloutfile = tempdir.path + "/out.h"
        # write them to outfile
        for propname, propvalue in data or []:
            propvalue = str(propvalue)
            result += "const char* {propname} = \"{propvalue}\";\n".format(**locals())
        result += "#endif\n"
        utils.basic.writetofile(fulloutfile, result)
        return results.Filestructure(fulloutfile)
