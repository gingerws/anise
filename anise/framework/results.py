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

##@package anise.framework.results
##Typical anise result structures.

import os
import shutil
import atexit
from anise.framework import base
from anise.framework import projects
from anise.framework import globalvars
from anise.utils import logging


## This class is a special anise return type which is a file/folder (to be fetched to the current dir).
##
## Example:
##
## \verbatim
## def sometask():
##     somedir = create_some_directory_somehow()
##     return results.Filestructure(somedir)
## \endverbatim
class Filestructure:
    def __init__(self, path):
        self.path = os.path.abspath(path)

    ## Copies the complete filestructure or a subdirectory to a new destination.
    ##@param subpath if given, only this subdirectory will be copied.
    ##@param to if given, it specifies the destination path; if not given, a new directory in the current working
    ##          directory will be used.
    def dl(self, subpath="", to=None):
        # prepare destination
        if not to:
            to = os.getcwd() + "/" + os.path.basename(self.path)
            if os.path.exists(to):  # we don't do that if we have an explicit destination
                logging.logwarning("removing old "+to, printcaller=False)
                if os.path.isdir(to):
                    shutil.rmtree(to)
                else:
                    os.unlink(to)
        # copy
        fullpath = os.path.abspath(self.path + "/" + subpath)
        if os.path.isfile(fullpath):
            dto = os.path.dirname(to)
            if not os.path.isdir(dto):
                os.makedirs(dto)
            shutil.copy2(fullpath, to)
        elif os.path.isdir(fullpath):
            if not os.path.isdir(to):
                os.makedirs(to)
            files = os.listdir(fullpath)
            while len(files) > 0:
                fn = files.pop(0)
                ff = fullpath + "/" + fn
                d = to + "/" + fn
                if os.path.islink(ff):
                    os.symlink(os.readlink(ff), d)
                elif os.path.isdir(ff):
                    if not os.path.isdir(d):
                        os.makedirs(d)
                    files += [fn+"/"+x for x in os.listdir(ff)]
                elif os.path.isfile(ff):
                    shutil.copy2(ff, d)
                else:
                    raise Exception("unknown thing: "+ff)
        else:
            raise Exception("not found: "+self.path)
        return to

    ## Returns a new (temporary) anise.framework.results.Filestructure clone with a new directory name.
    ##@param newname The name which the new root directory should get.
    def with_modified_rootname(self, newname):
        newtmp = TempDir()
        nname = newtmp.path + "/" + newname
        self.dl(to=nname)
        return Filestructure(nname)


## A special anise.framework.results.Filestructure which automatically creates a temporary directory in background.
##
## Example:
##
## \verbatim
## def sometask():
##     mytmp = results.TempDir()  # creates a temporary directory somewhere in no-man's-land
##     myfile = mytmp.path + "/somefile"
##     with open(myfile, "w") as f:
##         f.write("some content for our new file")
##     return mytmp
## \endverbatim
class TempDir(Filestructure):

    ##@param dirname An optional name which the root directory should get; if not given, it gets an random name.
    def __init__(self, dirname=None):
        i = 0
        path = None
        while path is None:
            _p = "/tmp/anise.{0}.{1}".format(os.getpid(), i)
            i += 1
            try:
                if not os.path.exists(_p):
                    os.mkdir(_p)
                    path = _p
                    atexit.register(self.delete)
            except Exception:
                pass
        self.origpath = path
        if dirname:
            path += "/" + dirname
            os.mkdir(path)
        Filestructure.__init__(self, path)

    def __enter__(self):
        return self

    ## Deletes the content from the hard drive.
    def delete(self):
        if globalvars.removetempdirs:
            try:
                shutil.rmtree(self.origpath)
            except Exception:
                pass

    def __exit__(self, type, value, traceback):
        self.delete()


## Provide a given file source description as an anise.framework.results.Filestructure object.
##@param source A file source description.
def source_to_filestructure(source):
    project = projects.currentproject()
    if source is None:
        return project.makerawpackage(dirname="x")
    elif isinstance(source, base.TaskExecution):
        return source.execute()
    elif isinstance(source, Filestructure):
        return source
    elif isinstance(source, str):
        return Filestructure(project.projectdir + "/" + source)
    elif isinstance(source, list):
        f = TempDir()
        for part in source:
            source_to_filestructure(part).dl(to=f.path)
        return f
    elif isinstance(source, dict):
        f = TempDir()
        for dd in source.keys():
            fd = os.path.abspath(f.path + "/" + dd.format(name=project.name))
            if not os.path.isdir(os.path.dirname(fd)):
                os.makedirs(os.path.dirname(fd))
            srcfs = source_to_filestructure(source[dd])
            if os.path.isdir(srcfs.path):
                srcfs.dl(to=fd)
            elif os.path.isfile(srcfs.path):
                if not os.path.isdir(os.path.dirname(fd)):
                    os.makedirs(os.path.dirname(fd))
                shutil.copy2(srcfs.path, fd)
            else:
                raise Exception("unknown thing: "+srcfs.path)
        return f
    else:
        raise Exception("not understood source: "+str(source))
