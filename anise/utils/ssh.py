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

##@package anise.utils.ssh
##Utilities for ssh usage
import shlex

from anise.utils import basic


## Executes a command via ssh.
def call(dst, cmd, options=[], port=22, identityfile=None):
    idfileoptions = ["-i", identityfile] if identityfile else []
    r, o = basic.call("ssh", "-p", port, *(options+idfileoptions+[dst, cmd]),
                      raise_on_errors="unable to call ssh")
    return o


## Mounts a volume via ssh.
class Mount(basic.Mount):

    ##@param src The remote mount source (an ssh address like user@machine).
    ##@param dst The local mount destination.
    ##@param options Optional additional mount options.
    ##@param port Optional tcp port.
    ##@param identityfile Optional identity file for authentication.
    def __init__(self, src, dst, options=[], port=22, identityfile=None):
        idfileoptions = ["-o", "IdentityFile="+shlex.quote(identityfile)] if identityfile else []
        basic.Mount.__init__(self, src, dst, options + idfileoptions + ["-p", port],
                             mounter=["sshfs"], unmounter=["fusermount", "-u"], needsroot=False)


## Copies a local directory to a remote place via ssh.
##@param src The source.
##@param dst The destination.
##@param options Optional additional mount options.
##@param port Optional tcp port.
##@param identityfile Optional identity file for authentication.
def copy(src, dst, options=[], port=22, identityfile=None):
    idfileoptions = ["-o", "IdentityFile="+shlex.quote(identityfile)] if identityfile else []
    r, o = basic.call("scp", "-r", "-P", port, *(options+idfileoptions+[src,dst]),
                      raise_on_errors="unable to call ssh")
