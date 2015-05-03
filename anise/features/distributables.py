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

##@package anise.features.distributables
## Defining distributables (installation packages for target systems, ...).
##
## Makes the following new functionality available:
## - provides a method for adding distributables groups to a pool
## - automatically adding a download section to the homepage

import hashlib
import os
import shutil

from anise.framework import projects
from anise.framework import features
from anise.framework import results
from anise import utils


class _Pool:

    def __init__(self):
        self.list = []

    def addgroup(self, task, **params):
        self.list.append(FileGroup(task, **params))


## A file group.
class FileGroup:

    ##@param task The task implementation which generates the download group content.
    ##@param prms Additional parameters for calling `task`.
    def __init__(self, task, **prms):
        self.buildparams = {}
        self.task = task
        self.description = None
        self.linkto = None
        for k in prms.keys():
            v = prms[k]
            if k == "name":
                self.name = v
            elif k == "description":
                self.description = v
            elif k == "linkto":
                self.linkto = v
            else:
                self.buildparams[k] = v


@features.hook(features.HOOK_BEFORE_DEFINITION, provides=["distributable_groups"])
def _initproject():
    projects.currentproject().distributables.pool = _Pool()


@features.hook(features.HOOK_BEFORE_EXECUTION)
def _add_homepage_section():
    project = projects.currentproject()
    def my_homepage_section(homepage, sourcedir, version, head4, bannerimage, *kwargs):
        if len(project.distributables.pool.list) > 0:
            downloads = "The following content is available for download.\n\n" + \
                        "Note: *Use at your own risk!*\n\n"
            for dlgroup in project.distributables.pool.list:
                downloads += "<div class='downloadgroup'>\n"
                downloads += "#### " + dlgroup.name
                if dlgroup.description:
                    downloads += "\n<h6>" + dlgroup.description.encode('ascii', 'xmlcharrefreplace').decode() + "</h6>\n"
                downloads += "\n"
                for fn in dlgroup.task(**dlgroup.buildparams):
                    fn.dl(to=homepage.path)
                    bn = os.path.basename(fn.path)
                    hasher = hashlib.sha256()
                    fd = open(fn.path,"rb")
                    for line in fd.readlines():
                        hasher.update(line)
                    fd.close()
                    downloads += "<div class='download'>\n"
                    downloads += "[{bn}]({bn})\n".format(**locals())
                    downloads += "\n<h5>sha256sum: " + hasher.hexdigest() + "</h5>\n"
                    if hasattr(fn, "description"):
                        downloads += "\n<h6>" + fn.description.encode('ascii', 'xmlcharrefreplace').decode() + "</h6>\n"
                    downloads += "</div>\n"
                    if dlgroup.linkto is not None:
                        projects.currentproject().addhook(features.loadfeature("homepage").featuremodule.HOOK_UPLOAD_HOMEPAGE_COLLECTLINKS,
                                                          (lambda x: (lambda:x))([(bn, dlgroup.linkto)]))
                downloads += "\n</div>\n"
            return downloads
    project.homepage.sections.add(5000, "Downloads", my_homepage_section)
