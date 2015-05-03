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

##@package anise.features.releasing
## Generic releasing task. The main usage is providing a hook for other features to mount something there.
##
## Makes the following new functionality available:
## - release process framework via tasks.release
## - adding custom release subtasks into the process

from anise.framework import projects
from anise.framework import features
from anise.framework import results
from anise import utils


HOOK_RELEASE = "RELEASE"


class _Releasetasks:

    ## Specifies a new task and adds it into the releasing chain.
    ##@param The task implementation to add.
    ##@param Additional parameters for calling that task.
    def add(self, task, **params):
        projects.currentproject().addhook(HOOK_RELEASE, task, params)


@features.hook(features.HOOK_BEFORE_DEFINITION, provides=["releasing"])
def _initproject():
    projects.currentproject().releasing.releasetasks = _Releasetasks()
    projects.currentproject().release = tasks.release


class tasks:

    ## Releases the project. Mostly this is executing all registered hooks for this event.
    @staticmethod
    @utils.logging.log_start_stop("Releasing")
    def release():
        for fct in projects.currentproject().gethooks(HOOK_RELEASE):
            fct()
