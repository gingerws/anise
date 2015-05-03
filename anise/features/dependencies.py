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

##@package anise.features.dependencies
## Specifying third-party packages which are required by the project in some way.
##
## Makes the following new functionality available:
## - provides a method for adding project dependencies
## - task for getting a piece of documentation source describing the dependencies
## - some enumerations
## - automatically adding a documentation section to the homepage

import hashlib
import os
import shutil

from anise.framework import projects
from anise.framework import features
from anise.framework import results
from anise import utils


## Enumeration of different types of dependencies.
class Type:
    Included = "included"
    Required = "required"
    Required_HasAlternatives = "required (has alternatives)"
    Recommended_HasAlternatives = "recommended (maybe has alternatives)"
    Optional = "optional"


## A dependency
class Dependency:

    def __init__(self, type, objectname=None, comment="", icon=None, visible=True, displayname=None, **kwargs):
        self.type = type
        self.objectname = objectname
        self.comment = comment
        self.icon = icon
        self.visible = visible
        self.displayname = displayname or objectname
        for k in kwargs:
            setattr(self, k, kwargs[k])


class _Pool:

    def __init__(self):
        self.list = []

    def add(self, dependency):
        self.list.append(dependency)


@features.hook(features.HOOK_BEFORE_DEFINITION, provides=["pdependencies"])
def _initproject():
    projects.currentproject().dependencies.pool = _Pool()
    projects.currentproject().getdependencydocument = tasks.getdependencydocument


@features.hook(features.HOOK_BEFORE_EXECUTION, provides=["pdependencies"])
def _add_homepage_section():
    project = projects.currentproject()
    def my_homepage_section(homepage, sourcedir, version, head4, bannerimage, *kwargs):
        return "<div class='deps'>" + project.getdependencydocument() + "</div>"
    project.homepage.sections.add(4000, "Dependencies", my_homepage_section)


class tasks:

    ##Creates a Markdown documentation string which describes the project dependencies in a human-readable form.
    ##
    ## It is mostly used for including it into Doxygen documentation source.
    @staticmethod
    def getdependencydocument():
        project = projects.currentproject()
        depslist = [x for x in project.dependencies.pool.list if x.visible]
        if len(depslist) == 0:
            dependencies = "There are no dependencies.\n"
        elif len(depslist) == 1:
            dependencies = ("There is an external part which is used by {name}. " +
                            "Many thanks to the project and all participants.\n").format(name=project.name)
        else:
            dependencies = ("There are external parts which are used by {name}. " +
                            "Many thanks to the projects and all participants.\n").format(name=project.name)
        for dependency in depslist:
            icon = dependency.icon
            comment = dependency.comment
            obj = dependency.displayname
            dtype = dependency.type
            if icon is None or icon == "":
                icon = "nullicon"
            dlm = ": " if (len(comment) > 0) else ""
            obj = obj.replace("`", "'")
            dependencies += "\n\image html \"icons/{icon}.png\"\n `{obj}` *{dtype}* {dlm}{comment}\n".format(**locals())
        return dependencies


