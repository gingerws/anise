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

##@package anise.features.packages.android
##Creation of Android distribution packages.
##
## Makes the following new functionality available:
## - task for creating Android packages.
## - task for keeping the Android project file up-to-date

from anise.framework import projects
from anise.framework import features
from anise.framework import results
from anise import utils
from xml.dom import minidom


class tasks:

    ## Builds an Android package with Ant.
    ##@param androidpath Full path to the `android` tool (something like `.../android-sdk/tools/android`).
    ##@param relpath The root path of the android project, relative to `source`s root.
    ##@param targetname Name of the Ant target to build.
    @staticmethod
    @utils.logging.log_start_stop("Creating Android package")
    def package_with_ant(androidpath, source=None, relpath="", targetname="debug"):
        project = projects.currentproject()
        srcfs = results.source_to_filestructure(source)
        return [utils.packaging.buildandroidpackage_with_ant(name=project.name, version=project.getversion(),
                                                             projectroot=srcfs.path+"/"+relpath,
                                                             targetname=targetname, androidpath=androidpath)]


    ## Updates some project data (like version number) in the `AndroidManifest.xml`.
    ##@param outfile The folder which holds the `AndroidManifest.xml`. Can be absolute or relative to the anise project
    ##               directory.
    ##@param data unused.
    @staticmethod
    def inject_projectdata_to_androidmanifest(outfile, data):
        project = projects.currentproject()
        if outfile.startswith("/"):
            manifest = outfile + "/AndroidManifest.xml"
        else:
            manifest = project.projectdir + "/" + outfile + "/AndroidManifest.xml"
        version = project.getversion()
        _version = version.split(".")
        _version2 = []
        if len(_version) > 1:
            _version2.append(_version[0])
        if len(_version) > 2:
            _version2.append(_version[1])
        _version2.append(_version[-1])
        _version2 = ["00000"+x for x in _version2]
        versioncode = int(_version2[0][-2:] + _version2[1][-2:] + _version2[2][-5:])
        doc = minidom.parse(manifest)
        doc.documentElement.attributes["android:versionName"] = version
        doc.documentElement.attributes["android:versionCode"] = str(versioncode)
        with open(manifest, "w") as f:
            doc.writexml(f, encoding="utf-8")
