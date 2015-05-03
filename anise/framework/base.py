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

##@package anise.framework.base
## Some things intended to be used from the project description file. The engine automatically import everything from
## here into the execution context of the project description file, so they are automatically available there.


## Holds a function and some parameters for calling later on (like a delegate).
class TaskExecution:

    ##@param task The task implementation for execution.
    def __init__(self, task, **kwargs):
        self.task = task
        self.params = kwargs

    def execute(self, **kwargs):
        kwargs.update(self.params)
        return self.task(**kwargs)
