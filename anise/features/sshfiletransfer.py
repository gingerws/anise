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

##@package anise.features.sshfiletransfer
## File transfers via ssh.
##
## Makes the following new functionality available:
## - uploading directories via ssh

import os
import random
import shlex
import shutil
import sys

from anise.framework import projects
from anise.framework import features
from anise.framework import results
from anise import utils

_homepagefeature = features.loadfeature("homepage").featuremodule


class tasks:

    ## Deploys the homepage to a web server via ssh.
    ##@param server The server description name (a prefix for some property names).
    @staticmethod
    def upload(source=None, server="homepage", collectlinkshook=_homepagefeature.HOOK_UPLOAD_HOMEPAGE_COLLECTLINKS):
        project = projects.currentproject()
        hp = results.source_to_filestructure(source).with_modified_rootname(project.name)
        utils.logging.loginfo("Deploying project homepage to server")
        hpdir = hp.path
        srvidentityfile = getattr(project, server + "_serveridentityfile", None)
        srvtransferstrategy = getattr(project, server + "_servertransferstrategy", None)
        srvport = getattr(project, server + "_serverport", None)
        srvuser = getattr(project, server + "_serveruser", None)
        srvhostname = getattr(project, server + "_serverhostname", None)
        srvdestination = getattr(project, server + "_serverdestination", None)
        srvindexpattern = getattr(project, server + "_serverindexpattern", None)
        sshtgt = "{}@{}:/{}".format(srvuser, srvhostname, srvdestination)
        if srvtransferstrategy == "tar":
            with results.TempDir() as tartmpdir:
                tarfilename = "hp.{0}.{1}.tgz".format(os.getpid(), random.randrange(sys.maxsize))
                utils.basic.maketarball(hpdir, tartmpdir.path+"/"+tarfilename)
                with results.TempDir() as tmpdir:
                    with utils.ssh.Mount(sshtgt, tmpdir.path, port=srvport, identityfile=srvidentityfile):
                        serverroot = tmpdir.path
                        tartmpdir.dl(subpath=tarfilename, to=serverroot)
                        p = serverroot + "/" + project.name
                        try:
                            appidx = utils.basic.readfromfile(serverroot + "/_apps.txt")
                        except Exception:
                            appidx = ""
                        if not "/{}/".format(project.name) in appidx:
                            appidx += srvindexpattern.format(name=project.name)
                            utils.basic.writetofile(serverroot + "/_apps.txt", appidx)
                        pdst = shlex.quote(srvdestination+"/"+project.name)
                        dst = shlex.quote(srvdestination)
                        tarf = shlex.quote(tarfilename)
                        utils.ssh.call(srvuser+"@"+srvhostname,
                                       "rm -rf {pdst} ; cd {dst} && tar xfz {tarf} && rm {tarf}".format(**locals()),
                                       port=srvport, identityfile=srvidentityfile)
        else:
            with results.TempDir() as tmpdir:
                with utils.ssh.Mount(sshtgt, tmpdir.path, port=srvport, identityfile=srvidentityfile):
                    serverroot = tmpdir.path
                    p = serverroot + "/" + project.name
                    if os.path.exists(p):
                        shutil.rmtree(p)
                    hp.dl(to=p)
                    try:
                        appidx = utils.basic.readfromfile(serverroot + "/_apps.txt")
                    except Exception:
                        appidx = ""
                    if not "/{}/".format(project.name) in appidx:
                        appidx += srvindexpattern.format(name=project.name)
                        utils.basic.writetofile(serverroot + "/_apps.txt", appidx)
        sshcmd = ""
        for fct in projects.currentproject().gethooks(collectlinkshook):
            for src, tgt in fct():
                ssrc = shlex.quote(srvdestination + "/" + project.name + "/" + src)
                stgt = shlex.quote(srvdestination + "/" + project.name + "/" + tgt)
                sshcmd += "rm {stgt};ln -s {ssrc} {stgt};".format(**locals())
        if len(sshcmd) > 0:
            sshcmd = sshcmd[:-1]
            utils.ssh.call(srvuser+"@"+srvhostname, sshcmd, port=srvport, identityfile=srvidentityfile)


