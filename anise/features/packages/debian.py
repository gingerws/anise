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

##@package anise.features.packages.debian
##Creation of Debian distribution packages.
##
## Makes the following new functionality available:
## - task for creating a Debian package

import os
import shutil

from anise.framework import projects
from anise.framework import features
from anise.framework import results
from anise import utils


## Enumeration for Debian's categories for software packages.
class Category:
    ApplicationsAccessibility = ("Applications/Accessibility", "System")
    ApplicationsAmateurradio = ("Applications/Amateur Radio", "Utility")
    ApplicationsDatamanagement = ("Applications/Data Management", "System")
    ApplicationsEditors = ("Applications/Editors", "Utility")
    ApplicationsEducation = ("Applications/Education", "Education")
    ApplicationsEmulators = ("Applications/Emulators", "System")
    ApplicationsFilemanagement = ("Applications/File Management", "System")
    ApplicationsGraphics = ("Applications/Graphics", "Graphics")
    ApplicationsMobiledevices = ("Applications/Mobile Devices", "Utility")
    ApplicationsNetwork = ("Applications/Network", "Network")
    ApplicationsNetworkCommunication = ("Applications/Network/Communication", "Network")
    ApplicationsNetworkFiletransfer = ("Applications/Network/File Transfer", "Network")
    ApplicationsNetworkMonitoring = ("Applications/Network/Monitoring", "Network")
    ApplicationsNetworkWebbrowsing = ("Applications/Network/Web Browsing", "Network")
    ApplicationsNetworkWebnews = ("Applications/Network/Web News", "Network")
    ApplicationsOffice = ("Applications/Office", "Office")
    ApplicationsProgramming = ("Applications/Programming", "Development")
    ApplicationsProjectmanagement = ("Applications/Project Management", "Development")
    ApplicationsScience = ("Applications/Science", "Education")
    ApplicationsScienceAstronomy = ("Applications/Science/Astronomy", "Education")
    ApplicationsScienceBiology = ("Applications/Science/Biology", "Education")
    ApplicationsScienceChemistry = ("Applications/Science/Chemistry", "Education")
    ApplicationsScienceDataanalysis = ("Applications/Science/Data Analysis", "Education")
    ApplicationsScienceElectronics = ("Applications/Science/Electronics", "Education")
    ApplicationsScienceEngineering = ("Applications/Science/Engineering", "Education")
    ApplicationsScienceGeoscience = ("Applications/Science/Geoscience", "Education")
    ApplicationsScienceMathematics = ("Applications/Science/Mathematics", "Education")
    ApplicationsScienceMedicine = ("Applications/Science/Medicine", "Education")
    ApplicationsSciencePhysics = ("Applications/Science/Physics", "Education")
    ApplicationsScienceSocial = ("Applications/Science/Social", "Education")
    ApplicationsShells = ("Applications/Shells", "System")
    ApplicationsSounds = ("Applications/Sound", "AudioVideo")
    ApplicationsSystem = ("Applications/System", "System")
    ApplicationsSystemAdministration = ("Applications/System/Administration", "System")
    ApplicationsSystemHardware = ("Applications/System/Hardware", "System")
    ApplicationsSystemLanguageenvironment = ("Applications/System/Language Environment", "System")
    ApplicationsSystemMonitoring = ("Applications/System/Monitoring", "System")
    ApplicationsSystemPackagemanagement = ("Applications/System/Package Management", "System")
    ApplicationsSystemSecurity = ("Applications/System/Security", "System")
    ApplicationsTerminalemulators = ("Applications/Terminal Emulators", "System")
    ApplicationsText = ("Applications/Text", "Utility")
    ApplicationsTvandradio = ("Applications/TV and Radio", "AudioVideo")
    ApplicationsViewers = ("Applications/Viewers", "Utility")
    ApplicationsVideo = ("Applications/Video", "AudioVideo")
    ApplicationsWebdevelopment = ("Applications/Web Development", "Development")
    GamesAction = ("Games/Action", "Game")
    GamesAdventure = ("Games/Adventure", "Game")
    GamesBlocks = ("Games/Blocks", "Game")
    GamesBoard = ("Games/Board", "Game")
    GamesCard = ("Games/Card", "Game")
    GamesPuzzles = ("Games/Puzzles", "Game")
    GamesSimulation = ("Games/Simulation", "Game")
    GamesStrategy = ("Games/Strategy", "Game")
    GamesTools = ("Games/Tools", "Game")
    GamesToys = ("Games/Toys", "Game")
    Help = ("Help", "System")
    ScreenSaving = ("Screen/Saving", "System")
    ScreenLocking = ("Screen/Locking", "System")


## Description for Debian services to be included in a package.
class ServiceDescription:

    ##@param name The display name.
    ##@param command The command to be executed.
    def __init__(self, name, command):
        self.name = name
        self.command = command


class MenuEntry(utils.packaging.DebianPackageMenuEntry):
    pass


class tasks:

    ## Builds a Debian package.
    ##@ param dependencies A list of Debian dependencies for installation on target machines.
    ##@ param executablelinks A dict for links to executables for deployment on target machines.
    ##@ param menuentries A list of menu entries for creation on target machines.
    ##@ param services A list of services for deployment on target machines.
    ##@ param prerm Piece of bash script executed before removal of the package on target machines.
    ##@ param postinst Piece of bash script executed after installation of the package on the target machines.
    ##@ param architecture The target architecture name.
    @staticmethod
    @utils.logging.log_start_stop("Creating debian package")
    def debpackage(source=None, dependencies=[], executablelinks={}, menuentries=[], services=[],
                   prerm="", postinst="", architecture="all"):
        project = projects.currentproject()
        srcfs = results.source_to_filestructure(source)
        srcsrcfs = project.makerawpackage(project.name)
        for src, dst in [("README", "/usr/share/doc/{name}/README"), ("README.pdf", "/usr/share/doc/{name}/README.pdf")]:
            s = srcsrcfs.path + "/" + src
            d = os.path.abspath(srcfs.path + "/" + dst.format(name=project.name))
            if os.path.isfile(s):
                if not os.path.isdir(os.path.dirname(d)):
                    os.makedirs(os.path.dirname(d))
                srcsrcfs.dl(subpath=src, to=d)
        dependencies = list(dependencies) + project.dependencies.pool.list
        dependencies = [x for x in dependencies if hasattr(x, "debian")]
        dependencies = [dependency for dependencyitem in dependencies for dependency in dependencyitem.debian]
        return [utils.packaging.builddebpackage(name=project.name, version=project.getversion(),
                                                image="image", licensename=project.license.namedebian,
                                                authors=project.authors[0], email=project.email, summary=project.summary,
                                                description=project.longdescription, section="web",
                                                menuentries=menuentries, executablelinks=executablelinks,
                                                dependencies=dependencies, services=services,
                                                architecture=architecture, websiteurl=project.getwebsiteurl(),
                                                rawpkgpath=srcfs.path, projectfsroot=project.projectdir, prerm=prerm,
                                                postinst=postinst)]


    ## Returns a filtered set of files for a Debian program directory (no documentation, license, tests, ...).
    @staticmethod
    def only_programfiles(source=None):
        srcfs = results.source_to_filestructure(source).with_modified_rootname("x")
        for remv in ["README", "README.pdf", "LICENSE", "_meta", "_test"]:
            x = srcfs.path + "/" + remv
            if os.path.isfile(x):
                os.unlink(x)
            elif os.path.isdir(x):
                shutil.rmtree(x)
        return srcfs
