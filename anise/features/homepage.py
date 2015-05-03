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

##@package anise.features.homepage
## Project homepage generation.
##
## Makes the following new functionality available:
## - provides a method for adding sections with content to the homepage
## - task for creating a project homepage

import os
import shutil

from anise.framework import projects
from anise.framework import features
from anise.framework import results
from anise import utils


HOOK_UPLOAD_HOMEPAGE_COLLECTLINKS = "UPLOAD_HOMEPAGE_COLLECTLINKS"

class _Sections:

    def __init__(self):
        self.list = []

    def add(self, index, key, text):
        self.list.append((index, key, text))


@features.hook(features.HOOK_BEFORE_DEFINITION, provides=["homepage"])
def _initproject():
    projects.currentproject().homepage.sections = _Sections()
    projects.currentproject().getbannerimage = tasks.getbannerimage


@features.hook(features.HOOK_BEFORE_EXECUTION, provides=["homepage"])
def _basic_homepage_sections():
    project = projects.currentproject()

    # About
    def my_homepage_section_about(homepage, sourcedir, version, head4, bannerimage, *kwargs):
        return project.longdescription
    project.homepage.sections.add(1000, "About", my_homepage_section_about)

    # Feedback
    def my_homepage_section_feedback(homepage, sourcedir, version, head4, bannerimage, *kwargs):
        return """If you have funny rants about {name} itself
or about some techniques it uses, some constructive feedback, a cool
patch or a mysterious problem, feel free to mail it to {email}.
""".format(name=project.name, email=project.email)
    project.homepage.sections.add(8000, "Feedback", my_homepage_section_feedback)

    # Imprint
    def my_homepage_section_imprint(homepage, sourcedir, version, head4, bannerimage, *kwargs):
        return project.imprint.replace("[MAIL]", project.email)
    project.homepage.sections.add(9000, "Imprint", my_homepage_section_imprint)


class tasks:

    ##Writes the developer documentation, as specified in the project description, and returns it as Filestructure.
    @staticmethod
    @utils.logging.log_start_stop("Creating the project homepage")
    def makehomepage():
        project = projects.currentproject()
        homepage = results.TempDir(dirname=project.name + "-homepage")
        if not getattr(project, "omitsyncvcs", False):
            project.syncversioncontrolsystem(commitmessage="automated commit for make homepage")
        rawpkg = project.makerawpackage(dirname=project.name)
        sourcedir = rawpkg.path
        bannerimage = project.projectdir + "/" + project.getbannerimage()
        utils.basic.writetofile(homepage.path + "/license", project.license.getlicensetext())
        maturity = project.getprojectstatusdescription(True) \
            if hasattr(project, "getprojectstatusdescription") else ""
        if len(maturity) > 0:
            maturity = "state: " + maturity
        versionstring = "current release: " + project.getversion()
        rawversionstring = project.getversion()
        sections = [y for y in
                        [(x[1], x[2](homepage, sourcedir, rawversionstring, maturity, bannerimage))
                            for x in sorted(project.homepage.sections.list)
                        ]
                        if y[1] is not None]
        utils.documentation.generate_doxygen_homepage(head1=project.name, head2=project.summary, head3=versionstring,
                                                      head4=maturity,
                                                      sourcedir=sourcedir, targetdir=homepage.path,
                                                      basecolor=project.basecolor,
                                                      bannerimage=bannerimage, sections=sections,
                                                      anisedatadir=project.anisedatadir)
        return homepage

    ##Determines the location of the banner image.
    @staticmethod
    def getbannerimage():
        _bi = "_meta/homepage_bannerimage.png"
        return _bi if os.path.isfile(projects.currentproject().projectdir + "/" + _bi) else None
