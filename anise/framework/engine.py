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

##@package anise.framework.engine
##The anise engine initializes all the anise plattform stuff and executes a task from a project file.
import importlib

from anise import utils
from anise.framework import features
from anise.framework import projects
from anise.framework import globalvars
import os
import sys


## Executes task 'taskname' from the project in 'projectfile'.
##@param taskname The name of the task to be executed.
##@param projectfile The path to the anise project description file. Their name is usually `_projectdesc`.
##@param projectdir The path to the project root directory.
##@param values Additional values to be set to the project object.
##@param loadfeaturesfrom List of paths where anise features shall be loaded from.
def execute(taskname, projectfile, projectdir, values, loadfeaturesfrom):
    # determine some constants like the project dir
    class _MyLocals: pass
    mylocals = _MyLocals()
    mylocals.projectfile = os.path.abspath(projectfile)
    mylocals.projectdir = os.path.abspath(projectdir)
    if mylocals.projectfile.startswith(mylocals.projectdir+"/"):
        mylocals.relativeprojectfile = mylocals.projectfile[len(mylocals.projectdir)+2:]
    else:
        mylocals.relativeprojectfile = mylocals.projectfile
    mylocals.anisedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    mylocals.anisedatadir = mylocals.anisedir + "/data"
    # prepare the project object
    _project = projects.Project({})
    projects.setcurrentproject(_project)
    g = importlib.import_module("anise.framework.imports").__dict__
    g["project"] = _project
    _project.append(mylocals.__dict__)
    _project.append(values)
    # load the features and put their stuff into the project object
    features.internals.resetfeatures()
    for featurepath in loadfeaturesfrom:
        features.internals.loadfeatures(featurepath)
    features.internals.injectdefaultstoproject(_project)
    features.internals.injecthookstoproject(_project)
    # execute the BEFORE_DEFINITION hooks
    for hook in _project.gethooks(features.HOOK_BEFORE_DEFINITION):
        hook()
    # execute the project description file
    with open(mylocals.projectfile, "r") as f:
        projectdesc = "".join(f.readlines())
    l = _project.__dict__
    exec(projectdesc, g, l)
    # load the local anise config
    _project.append(l)
    # execute the BEFORE_EXECUTION hooks
    for hook in _project.gethooks(features.HOOK_BEFORE_EXECUTION):
        hook()
    # apply the 'values' again
    _project.append(values)
    # execute the task
    res = getattr(_project, taskname)()
    # try to append a _targetdir hint to the task result
    if hasattr(_project, "targetdir"):
        try:
            res._targetdir = getattr(_project, "targetdir")
        except Exception:
            pass
    # return the task result
    return res


## \page commandline anise command line options
##
## The anise command line tool understands this syntax:
##
## \verbatim
## anise [taskname] [options]*
## \endverbatim
##
## The taskname refers to anything callable defined in the project description file. Options are all optional
## and can be the following:
##
## - `--setvalue [key] [value]` : Sets a value to the project object before execution
##
## - `--projectfile [file]` : Use this project file
##
## - `--loadfeaturesfrom [path1:...:pathn]` : Sets the paths for loading modules (separated by ":"; builtin
##    features by "builtin")
##
## - `--debug` : Enabled debug log output
##
## - `--keeptemp` : Don't remove the temporary stuff (for post-execution diagnostic)

## Parses the command line
def _cmdline(args):
    def nextparam():
        nonlocal c
        nonlocal args
        v = args[c] if c < len(args) else None
        c += 1
        return v

    c = 0
    values = {}
    projectfile = None
    taskname = None
    loadfeaturesfrom = "builtin:~/.anise/features:/var/lib/anise/features"
    if len(args) > 0 and args[0][0:2] != "--":
        taskname = args[0]
        c += 1
    _p = nextparam()
    while _p is not None:
        if _p[0:2] != "--": raise Exception("parse error: " + _p)
        p = _p[2:]
        if p == "setvalue":
            name = nextparam()
            value = nextparam()
            values[name] = value
        elif p == "projectfile":
            projectfile = nextparam()
        elif p == "loadfeaturesfrom":
            loadfeaturesfrom = nextparam()
        elif p == "debug":
            globalvars.logdebug = True
        elif p == "keeptemp":
            globalvars.removetempdirs = False
        else:
            raise Exception("unknown parameter: " + p)
        _p = nextparam()
    loadfeaturesfrom = [x for x in loadfeaturesfrom.split(":") if x.strip() != ""]
    loadfeaturesfrom = [((os.path.dirname(os.path.dirname(__file__)) + "/features") if x.strip() == "builtin" else x)
                        for x in loadfeaturesfrom]
    loadfeaturesfrom = [os.path.abspath(os.path.expanduser(x)) for x in loadfeaturesfrom]
    return utils.basic.dict2object(
        utils.basic.params2dict(taskname=taskname, values=values, projectfile=projectfile,
                                loadfeaturesfrom=loadfeaturesfrom))


## Can be used after executing a task in the anise engine for making a result file available in the target
## directory. Before you do so, all files created as result are in a temporary area, which will be flushed when
## the process terminates.
def extractfilesfromretval(r):
    if isinstance(r, dict):
        result = dict()
        for k in r:
            result[k] = extractfilesfromretval(r[k])
    elif isinstance(r, list) or isinstance(r, tuple):
        _result = list()
        for e in r:
            _result += [extractfilesfromretval(e)]
        if isinstance(r, tuple):
            result = tuple(_result)
        else:
            result = _result
    else:
        try:
            result = r.dl()
        except Exception:
            result = r
    return result


## The main method when called from command line. Parses command line arguments and executes the chosen task.
def main():
    cmdline = _cmdline(sys.argv[1:])
    taskname = cmdline.taskname
    startdir = os.getcwd()
    projectfile = cmdline.projectfile
    if projectfile is None and os.path.isfile("./_projectdesc"):
        projectfile = "./_projectdesc"
    elif projectfile is None and os.path.isfile("./_meta/_projectdesc"):
        projectfile = "./_meta/_projectdesc"
    if projectfile is not None:
        projectdir = os.path.dirname(projectfile)
        if projectdir.endswith("/_meta"):
            projectdir = projectdir[0:-6]
    else:
        raise Exception("no project file found.")
    if taskname is None:
        taskname = "DEFAULT"
    retval = None
    retcode = 0
    try:
        retval = execute(taskname, projectfile, projectdir, cmdline.values, cmdline.loadfeaturesfrom)
    except BaseException as e:
        retcode = 1
        utils.logging.logexception(e)
    try:
        targetdir = retval._targetdir
    except Exception:
        targetdir = "."
    if not targetdir.startswith("/"):
        targetdir = startdir + "/" + targetdir
    os.chdir(targetdir)
    retval = extractfilesfromretval(retval)
    if retval:
        print(retval)
    sys.exit(retcode)
