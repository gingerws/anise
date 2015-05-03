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

##@package anise.features.filesystem
## Basic Filesystem tasks.
##
## Makes the following new functionality available:
## - tasks for doing stuff on filesystem level

import os
import shutil
import re
from anise.framework import results


class tasks:

    @staticmethod
    def filterbyfunction(acceptorfunction, source=None):
        srcfs = results.source_to_filestructure(source)
        result = results.TempDir()
        dirs = [(srcfs.path, "/")]
        while len(dirs) > 0:
            fulladir, reladir = dirs.pop()
            for afile in os.listdir(fulladir):
                fullafile = fulladir + "/" + afile
                relafile = reladir + "/" + afile
                tgtafile = result.path + "/" + relafile
                if acceptorfunction(relafile):
                    if os.path.isdir(fullafile):
                        os.mkdir(tgtafile)
                        dirs.append((fullafile, relafile))
                    else:
                        shutil.copy2(fullafile, tgtafile)
        return result

    @staticmethod
    def filterbyextension(source=None, exclude=None, include=None, casesensitive=False):
        def acceptorfunction(path):
            def _check(lst):
                ppath = path if casesensitive else path.lower()
                if lst is not None:
                    for x in lst:
                        if not x.startswith("."):
                            x = "." + x
                        if not casesensitive:
                            x = x.lower()
                        if ppath.endswith(x):
                            return True
                return False
            if _check(exclude):
                return False
            if _check(include):
                return True
            return (include is None)
        return tasks.filterbyfunction(acceptorfunction, source)

    @staticmethod
    def filterbyname(source=None, exclude=None, include=None, casesensitive=False):
        def acceptorfunction(path):
            def _check(lst):
                pname = os.path.basename(path if casesensitive else path.lower())
                if lst is not None:
                    for x in lst:
                        if pname == x:
                            return True
                return False
            if _check(exclude):
                return False
            if _check(include):
                return True
            return (include is None)
        return tasks.filterbyfunction(acceptorfunction, source)

    @staticmethod
    def filterbynamepattern(source=None, exclude=None, include=None, casesensitive=False):
        def acceptorfunction(path):
            def _check(lst):
                pname = os.path.basename(path if casesensitive else path.lower())
                if lst is not None:
                    for x in lst:
                        if re.match(x, pname):
                            return True
                return False
            if _check(exclude):
                return False
            if _check(include):
                return True
            return (include is None)
        return tasks.filterbyfunction(acceptorfunction, source)
