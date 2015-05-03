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

##@package anise.features.versioncontrol.svn
## Interoperability with the Subversion version control system.
##
## Makes the following new functionality available for Subversion controlled projects:
## - provides a method for getting a complete version number including svn revision
## - provides a method for creation of the raw package
## - provides syncing functionality between the repository and the working copy
## - provides a method for automatically enabling all this stuff


import os
import shutil
from anise.framework import projects
from anise.framework import features
from anise.framework import results
from anise import utils


## Configures a project for Subversion usage (binds some tasks so they get called).
def is_svn_controlled():
    project = projects.currentproject()
    project.sync = project.syncversioncontrolsystem = tasks.syncversioncontrolsystem
    project.getfullversion = tasks.getfullversion
    project.createrawpackage = tasks.createrawpackage


class tasks:

    ## Returns a complete version string, including the Subversion build number.
    @staticmethod
    def getfullversion():
        return projects.currentproject().version + utils.svn.getsvnrevision(projects.currentproject().projectdir).format()


    ##Generates a raw package by using the svn repository as a blueprint. This package is the basis for most (or all)
    ##of the other package types.
    ##@param dirname Specify which name the root directory shall get.
    @staticmethod
    @utils.logging.log_start_stop("Creating the raw source package")
    def createrawpackage(dirname):
        tmp = results.TempDir(dirname)
        l = utils.svn.listsvnrepo(projects.currentproject().projectdir)
        for e in l:
            full = projects.currentproject().projectdir + "/" + e
            tgtfull = tmp.path + "/" + e
            if os.path.islink(full):
                os.symlink(os.readlink(full), tgtfull)
            elif os.path.isdir(full):
                os.mkdir(tgtfull)
            elif os.path.isfile(full):
                shutil.copy2(full, tgtfull)
            else:
                raise utils.exceptions.BadFormatError("unknown thing: " + full)
        return tmp


    ##Synchronizes the local working copy with the project's svn repository.
    @staticmethod
    @utils.logging.log_start_stop("Synchronizing the working copy with the subversion repository")
    def syncversioncontrolsystem(commitmessage="", force=True):
        project = projects.currentproject()
        if force or (not getattr(project, "_vcssynced", False)):
            with utils.basic.ChDir(project.projectdir):
                utils.basic.call("svn", "update", raise_on_errors="errors in svn")
                utils.basic.call("svn", "commit", "-m", commitmessage, raise_on_errors="errors in svn")
                utils.basic.call("svn", "update", raise_on_errors="errors in svn")
            project._vcssynced = True
