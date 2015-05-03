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

##@package anise.features.licensing
## The project's license
##
## Makes the following new functionality available:
## - automatically adds a `LICENSE` file to the raw package
## - automatically instantiate the `license` if needed, so you are allowed to only write the class name
## - automatically adding a license section to the homepage if `license` is set


import inspect
import os
import shutil
import datetime

from anise.framework import projects
from anise.framework import features
from anise import utils


_packagesfeature = features.loadfeature("packages").featuremodule

## Base class for licenses. This interface is probably used by many features.
class BaseLicense:

    def __init__(self, namedebian=None, namepythonsetuputils=None, namefirefox=None, name=None, filename=None):
        self.namedebian = namedebian
        self.namepythonsetuputils = namepythonsetuputils
        self.namefirefox = namefirefox
        self.name = name if (name is not None) else self.__class__.__name__
        self.filename = filename

    ## Returns the full path of the license text file.
    def getfilename(self):
        if self.filename is None:
            self.filename = "//" + self.__class__.__name__
        if self.filename.startswith("//"):
            p = projects.currentproject().anisedatadir + "/licenses/" + self.filename
        elif self.filename.startswith("/"):
            p = self.filename
        else:
            p = projects.currentproject().projectdir + "/" + self.filename
        return os.path.abspath(p)

    ## Returns the full license text.
    def getlicensetext(self):
        project = projects.currentproject()
        with open(self.getfilename(), "r") as f:
            licensetext = f.read()
        authors = " and ".join(([", ".join(project.authors[0:-1])] if len(project.authors) > 1 else [])
                                + [project.authors[-1]])
        return licensetext \
            .replace("{{{year}}}", str(datetime.datetime.now().year)) \
            .replace("{{{authors}}}", authors) \
            .replace("{{{name}}}", project.name) \
            .replace("{{{contributors}}}", "")


@features.hook(_packagesfeature.HOOK_ENRICHRAWPACKAGE, provides=["license"])
def _writelicense(destdir):
    utils.basic.writetofile(destdir + "/LICENSE", projects.currentproject().license.getlicensetext())


@features.hook(features.HOOK_BEFORE_EXECUTION, provides=["license", "PRE"])
def _instantiatelicense():
    project = projects.currentproject()
    if inspect.isclass(project.license):
        project.license = project.license()


@features.hook(features.HOOK_BEFORE_EXECUTION, provides=["license"])
def _add_homepage_section():
    project = projects.currentproject()

    def my_homepage_section(homepage, sourcedir, version, head4, bannerimage, *kwargs):
        return """{name} is distributed under the terms of the [{license}](./license) license.
Read the [Dependencies](#dependencies) section for included third-party stuff.
""".format(name=project.name, license=project.license.name)
    project.homepage.sections.add(2000, "License", my_homepage_section)


class AGPLv3(BaseLicense):
    def __init__(self):
        BaseLicense.__init__(self, namedebian="AGPL-3", namepythonsetuputils="AGPL-3")


class GPLv3(BaseLicense):
    def __init__(self):
        BaseLicense.__init__(self, namedebian="GPL-3", namepythonsetuputils="GPL-3", namefirefox="GPL 3.0")


class AFLv3(BaseLicense):
    def __init__(self):
        BaseLicense.__init__(self, namedebian="AFL-3", namepythonsetuputils="AFL-3")


class Apache2(BaseLicense):
    def __init__(self):
        BaseLicense.__init__(self, namedebian="Apache-2", namepythonsetuputils="Apache-2")


class BSD3clause(BaseLicense):
    def __init__(self):
        BaseLicense.__init__(self, namedebian="BSD-3-clause", namepythonsetuputils="BSD-3-clause", name="BSD-3-clause")


class BSD2clause(BaseLicense):
    def __init__(self):
        BaseLicense.__init__(self, namedebian="BSD-2-clause", namepythonsetuputils="BSD-2-clause", name="BSD-2-clause")


class LGPLv3(BaseLicense):
    def __init__(self):
        BaseLicense.__init__(self, namedebian="LGPL-3", namepythonsetuputils="LGPL-3")


class MPLv11(BaseLicense):
    def __init__(self):
        BaseLicense.__init__(self, namedebian="MPL-1.1", namepythonsetuputils="MPL-1.1", name="MPL-1.1",
                             namefirefox="MPL 1.1")


class MPLv2(BaseLicense):
    def __init__(self):
        BaseLicense.__init__(self, namedebian="MPL-2", namepythonsetuputils="MPL-2", name="MPL-2.0",
                             namefirefox="MPL 2.0")


class CcBy3(BaseLicense):
    def __init__(self):
        BaseLicense.__init__(self, namedebian="CC-BY-3", namepythonsetuputils="CC-BY-3", name="CC-BY-3")


class CcBySa3(BaseLicense):
    def __init__(self):
        BaseLicense.__init__(self, namedebian="CC-BY-SA-3", namepythonsetuputils="CC-BY-SA-3", name="CC-BY-SA-3")


class CcByNd3(BaseLicense):
    def __init__(self):
        BaseLicense.__init__(self, namedebian="CC-BY-ND-3", namepythonsetuputils="CC-BY-ND-3", name="CC-BY-ND-3")


class CcByNc3(BaseLicense):
    def __init__(self):
        BaseLicense.__init__(self, namedebian="CC-BY-NC-3", namepythonsetuputils="CC-BY-NC-3", name="CC-BY-NC-3")


class CcByNcSa3(BaseLicense):
    def __init__(self):
        BaseLicense.__init__(self, namedebian="CC-BY-NC-SA-3", namepythonsetuputils="CC-BY-NC-SA-3",
                             name="CC-BY-NC-SA-3")


class CcByNcNd3(BaseLicense):
    def __init__(self):
        BaseLicense.__init__(self, namedebian="CC-BY-NC-ND-3", namepythonsetuputils="CC-BY-NC-ND-3",
                             name="CC-BY-NC-ND-3")


class Cc0v1(BaseLicense):
    def __init__(self):
        BaseLicense.__init__(self, namedebian="CC0-1", namepythonsetuputils="CC0-1", name="CC0-1")


class Artistic1(BaseLicense):
    def __init__(self):
        BaseLicense.__init__(self, namedebian="Artistic-1", namepythonsetuputils="Artistic-1")


class MIT(BaseLicense):
    def __init__(self):
        BaseLicense.__init__(self, namedebian="MIT", namepythonsetuputils="MIT")


class PublicDomain(BaseLicense):
    def __init__(self):
        BaseLicense.__init__(self, namedebian="public-domain", namepythonsetuputils="public-domain",
                             namefirefox="public domain")

