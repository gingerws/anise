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

##@package anise.features.imagegalleries
## Image galleries.
##
## Makes the following new functionality available:
## - provides a method for adding image galleries to the pool of image galleries
## - automatically adding a image gallery section to the homepage


import os
import shutil

from anise.framework import projects
from anise.framework import features


class _Pool:

    def __init__(self):
        self.list = []

    def add(self, name, gallerydir):
        self.list.append((name, gallerydir))


@features.hook(features.HOOK_BEFORE_DEFINITION, provides=["imagegalleries"])
def _initproject():
    projects.currentproject().imagegalleries.pool = _Pool()
    projects.currentproject().getimagegallery = tasks.getimagegallery

@features.hook(features.HOOK_BEFORE_EXECUTION, provides=["imagegalleries"])
def _add_homepage_section():
    project = projects.currentproject()

    def my_homepage_section(homepage, sourcedir, head3, head4, bannerimage, *kwargs):
        if len(project.imagegalleries.pool.list) > 0:
            galleries = ""
            i = 0
            for galleryname, gallerydir in project.imagegalleries.pool.list:
                galleries += "\n#### {galleryname}\n".format(galleryname=galleryname)
                ngallerydir = "gallery{0}/".format(i)
                shutil.copytree(project.projectdir + "/" + gallerydir, homepage.path + "/" + ngallerydir)
                for (ipath, ititle) in project.getimagegallery(homepage.path + "/" + ngallerydir):
                    galleries += "\image html \"{ipath}\" \"{ititle}\"\n".format(ipath=ipath,
                                                        ititle=ititle.replace("\n", " ").replace('"', "''"))
                i += 1
            return galleries
    project.homepage.sections.add(6500, "Gallery", my_homepage_section)

class tasks:

    ##Returns a data structure which contains all information for building one image gallery.
    ##@param imgdir The absolute path to the directory which contains the gallery.
    @staticmethod
    def getimagegallery(imgdir):
        result = []
        while imgdir.endswith("/"):
            imgdir = imgdir[:-1]
        for img in os.listdir(imgdir):
            if img.endswith(".png") or img.endswith(".jpg") or img.endswith(".jpeg"):
                fimg = imgdir+"/"+img
                fimgdesc = fimg+".txt"
                desc = ""
                if os.path.isfile(fimgdesc):
                    with open(fimgdesc, "r") as f:
                        desc = "\n".join(f.readlines())
                result += [(os.path.basename(imgdir)+"/"+img, desc)]
            result.sort(key=lambda x: x[0])
        return result
