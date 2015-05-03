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

##@package anise.utils.basic
##Basic helpers for filesystem and other operating system related stuff

from . import exceptions

import atexit
import hashlib
import os
import subprocess
import socket
import random
import time


## writes some content to a file
def writetofile(filename, content):
    with open(filename, "w") as f:
        f.write(content)


## reads the content from a file
def readfromfile(filename, onestring=True):
    with open(filename, "r") as f:
        r = f.readlines()
    if onestring:
        r = "".join(r)
    return r


## creates a directory path (recursively)
def mkdirs(dname):
    if not os.path.isdir(dname):
        os.makedirs(dname)


def dict2object(d):
    class aniseobject:
        pass

    r = aniseobject()
    for k in d:
        setattr(r, k, d[k])
    return r


def params2dict(**d):
    return d


## makes a tarball from a given directory structure
def maketarball(rootdir, tarname):
    with ChDir(rootdir + "/.."):
        rootname = rootdir[rootdir[:-1].rfind("/") + 1:] # incl. some magic for / at the end
        (rv, ou) = call(["tar", "cfz", tarname, rootname], raise_on_errors=True)


## executes a command line
def call(*cmdline, shell=False, decode=True, raise_on_errors=None):
    r = b""
    ret = 0
    try:
        if len(cmdline) == 1: cmdline = cmdline[0]
        r = subprocess.check_output(cmdline, stderr=subprocess.STDOUT, shell=shell)
    except subprocess.CalledProcessError as err:
        ret = err.returncode
        r = err.output
    if raise_on_errors and (ret != 0):
        raise exceptions.ProcessExecutionFailedError(
            str(raise_on_errors) + ": " + str(cmdline) + ": " + r.decode(errors='replace').strip()
        )
    return ret, (r.decode().strip() if decode else r)


## returns a random and (statistically nearly) unique string
def getuniqueidentifier():
    r = socket.gethostname() + "".join([str(random.random()) for x in range(4)])
    return hashlib.sha224(r.encode()).hexdigest()


## Wraps a string, so all lines are not larger than 80 characters.
def linewrap(txt):
    r = ""
    w = 80
    for s in txt.split("\n"):
        if len(s) == 0: r += "\n"
        while len(s) > 0:
            if len(s) > w:
                sp = s[:w].rfind(" ")
                if sp == -1:
                    sp = w
            else:
                sp = len(s)
            r += s[:sp] + "\n"
            s = s[sp:].strip()
    return r


## Can be used to mount a volume. Can either be used automatically with the `with` keyword or manually.
class Mount:

    ##@param src Mount source.
    ##@param dst Mount destination.
    ##@param options Optional additional mount options.
    ##@param mounter Optional string list overriding the default mount call.
    ##@param unmounter Optional string list overriding the default unmount call.
    ##@param needsroot If this mount action will need root permissions.
    def __init__(self, src, dst, options=[], mounter=["mount"], unmounter=["umount"], needsroot=True):
        self.su = ["su", "-c"] if needsroot else []
        self.mounted = False
        self.src = src
        self.dst = dst
        self.options = options
        self.mounter = mounter
        self.unmounter = unmounter
        self.needsroot = needsroot

    ## Manually mount the volume.
    def mount(self):
        self.su = ["su", "-c"] if self.needsroot else []
        call(*(self.su + self.mounter + [self.src, self.dst] + self.options),
             raise_on_errors="unable to mount '{src}' to '{dst}'.".format(src=self.src, dst=self.dst))
        self.mounted = True

    def __enter__(self):
        self.mount()

    ## Manually unmount the volume.
    def unmount(self):
        if self.mounted:
            subprocess.call(["sync"])
            subprocess.call(["sync"])
            subprocess.call(["sync"])
            time.sleep(1)
            subprocess.call(self.su + self.unmounter + [self.dst])
            self.mounted = False

    def __exit__(self, type, value, traceback):
        self.unmount()


## Class for temporarily changing the current working directory in a scope of the `with` keyword.
class ChDir:

    def __init__(self, path):
        self.newpath = path

    def __enter__(self):
        self.oldpath = os.getcwd()
        os.chdir(self.newpath)
        return self

    def __exit__(self, type, value, traceback):
        os.chdir(self.oldpath)


## Strips a name to something very bare with only alphabetic letters.
##@param name The input name.
##@param lowercase If only lowercase characters are allowed.
def stripname(name, lowercase=True):
    res = ""
    for c in name:
        if c.lower() in "abcdefghijklmnopqrstuvwxyz":
            res += c
        elif c == "0": res += "Zero"
        elif c == "1": res += "One"
        elif c == "2": res += "Two"
        elif c == "3": res += "Three"
        elif c == "4": res += "Four"
        elif c == "5": res += "Five"
        elif c == "6": res += "Six"
        elif c == "7": res += "Seven"
        elif c == "8": res += "Eight"
        elif c == "9": res += "Nine"
    if lowercase:
        res = res.lower()
    return res


def createobjectstructure(root, newnames):
    class _AniseObject: pass
    parent = root
    parentparent = None
    for newname in newnames.split("."):
        parentparent = parent
        if hasattr(parent, newname):
            parent = getattr(parent, newname)
        else:
            _parent = _AniseObject()
            setattr(parent, newname, _parent)
            parent = _parent
    return parent, parentparent
