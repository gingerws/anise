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

##@package anise.features.packages.firefox
##Creation of Firefox addon packages.
##
## Makes the following new functionality available:
## - task for creating a Firefox addon package
## - task for keeping the Firefox addon project file up-to-date

import json
import anise.framework.projectinformations
from anise.framework import projects
from anise.framework import features
from anise.framework import results
from anise import utils


class tasks:

    ## Builds a Firefox addon.
    ##@param relpath Path of the firefox addon project relative to 'source's root.
    @staticmethod
    @utils.logging.log_start_stop("Creating Firefox addon package")
    def addonpackage(source=None, relpath=""):
        project = projects.currentproject()
        srcfs = results.source_to_filestructure(source)
        return [utils.packaging.buildfirefoxaddonpackage(name=project.name, version=project.getversion(),
                                                         projectroot=srcfs.path+"/"+relpath,
                                                         addonsdkpath=project.firefox_addonsdkpath)]


    ## Updates the `package.json` project file.
    ##@param outfile The directory which holds `package.json`, either absolute or relative to the anise project directory.
    ##@param data unused.
    @staticmethod
    def inject_projectdata_to_packagejson(outfile, data):
        project = projects.currentproject()
        if outfile.startswith("/"):
            packagejson = outfile + "/package.json"
        else:
            packagejson = project.projectdir + "/" + outfile + "/package.json"
        with open(packagejson, "r") as f:
            content = json.load(f)
        content["version"] = project.getversion()
        content["name"] = utils.basic.stripname(project.name)
        content["title"] = project.name
        content["license"] = project.license.namefirefox
        content["author"] = project.authors[0]
        content["contributors"] = project.authors[1:] + (project.contributors if hasattr(project, "contributors") else [])
        if hasattr(project, "getwebsiteurl"):
            content["homepage"] = project.getwebsiteurl()
        content["description"] = project.summary
        if "_PLEASE_NOTE" in content:
            del content["_PLEASE_NOTE"]
        newjson = json.dumps(content, f, indent=4)
        newjson = newjson[0:1] + """
        "_PLEASE_NOTE":                                                          [
        " The author of this project uses a tool, which automatically updates    ",
        " some parts of this file. This means that some values should not be     ",
        " changed here but in '{relativeprojectfile}'.{spaces1}",
        "   Homepage of the 'anise' tool:                                        ",
        "   {anisehomepage}{spaces2}"],

    """.format(relativeprojectfile=project.relativeprojectfile,
               spaces1=" "*(48-len(project.relativeprojectfile)),
               anisehomepage=anise.framework.projectinformations.homepage,
               spaces2=" "*(69-len(anise.framework.projectinformations.homepage))
        ) + newjson[2:]
        with open(packagejson, "w") as f:
            f.write(newjson)
