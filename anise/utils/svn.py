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

##@package anise.utils.svn
##Utilities for Subversion usage

from . import exceptions
from . import basic
import os
import re


class _Version:
    def __init__(self, build, tag):
        self.build = build
        self.tag = tag

    def isvalid(self):
        return self.tag != "unknown"

    def format(self):
        return ".{}{}".format(self.build, ("+%s" % (self.tag,)) if (self.tag != None) else "")


## Determines the revision number of the Subversion working copy.
def getsvnrevision(d):
    try:
        with basic.ChDir(d):
           (o, s) = basic.call("svnversion", raise_on_errors=True)
        m = re.search(r"^([0-9]+)(:[0-9]+)?([A-Z]+)?", s)
        build = int(m.group(1))
        changed = (m.group(2) != None) or (m.group(3) != None)
        tag = None
        if changed:
            tag = "alike"
    except exceptions.ProcessExecutionFailedError:
        build = "0"
        tag = "unknown"
    return _Version(build, tag)


## Determines the file tree of an Subversion repository.
##@param directory The directory you want to list.
def listsvnrepo(directory):
    (r, o) = basic.call("svn", "list", "-R", directory, "-r", "HEAD",
                        raise_on_errors="unable to call svn")
    res = [x for x in [a.strip() for a in o.split("\n")] if x != ""]
    return res

