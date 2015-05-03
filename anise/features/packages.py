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

##@package anise.features.packages
## Creating distribution packages.
##
## Makes the following new functionality available:
## - framework for enriching a raw package (and hook for adding custom functionality)
## - getting the project version number
## - creating tar source packages

import os
import shutil

from anise.framework import projects
from anise.framework import features
from anise import utils
from anise.framework import results


HOOK_ENRICHRAWPACKAGE = "ENRICHRAWPACKAGE"


@features.hook(features.HOOK_BEFORE_DEFINITION, provides=["packages"])
def _initproject():
    projects.currentproject().getwebsiteurl = tasks.getwebsiteurl
    projects.currentproject().getversion = tasks.getversion
    projects.currentproject().enrichrawpackage = tasks.enrichrawpackage
    projects.currentproject().makerawpackage = tasks.makerawpackage


class tasks:

    ## Returns the url from the project website.
    @staticmethod
    def getwebsiteurl():
        return None


    ## Adds certain stuff to a raw packages (as created by makerawpackage), like the license file.
    @staticmethod
    @utils.logging.log_start_stop("Enriching the rawpackage")
    def enrichrawpackage(packagedir):
        for hook in projects.currentproject().gethooks(HOOK_ENRICHRAWPACKAGE):
            hook(destdir=packagedir)


    ## Determines the version string of the project.
    @staticmethod
    def getversion():
        project = projects.currentproject()
        if not getattr(projects.currentproject(), "omitsyncvcs", False):
            projects.currentproject().syncversioncontrolsystem(commitmessage="automated anise commit", force=False)
        if hasattr(project, "_fullversion"):
            return project._fullversion
        elif hasattr(project, "getfullversion"):
            r = project.getfullversion()
            project._fullversion = r
            return r
        else:
            utils.logging.logwarning("No task 'getfullversion' found. Only using the base version.")
            r = project.version
            project._fullversion = r
            return r


    _makerawpackage_cache = None

    ## Builds a raw package in some flavour. This is used by other components (e.g. packaging) for creating
    ## distributable binary packages.
    @staticmethod
    @utils.logging.log_start_stop("Creating a raw package")
    def makerawpackage(dirname):
        project = projects.currentproject()
        targetdir = results.TempDir().path + "/" + dirname
        if tasks._makerawpackage_cache is None:
            tasks._makerawpackage_cache = project.createrawpackage(dirname=dirname)
            project.enrichrawpackage(packagedir=tasks._makerawpackage_cache.path)
        tasks._makerawpackage_cache.dl(to=targetdir)
        return results.Filestructure(targetdir)


    ## Builds a tarball which can be distributed. This is mostly a source package and is possibly not the most convenient
    ## package type for an end-user.
    @staticmethod
    @utils.logging.log_start_stop("Creating tar package")
    def tarpackage(source=None, namepostfix=None, pkgdescription=""):
        project = projects.currentproject()
        if not getattr(project, "omitsyncvcs", False):
            project.syncversioncontrolsystem(commitmessage="automated commit from anise")
        pkgroot = project.name + "-" + project.getversion() + (("-"+namepostfix) if namepostfix else "")
        tarname = results.TempDir().path + "/" + pkgroot + ".tgz"
        srcfs = results.source_to_filestructure(source).with_modified_rootname(pkgroot)
        utils.basic.maketarball(rootdir=srcfs.path, tarname=tarname)
        result = results.Filestructure(tarname)
        result.description = pkgdescription
        return [result]
