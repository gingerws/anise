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

##@package anise.features.documentation
## Project documentation.
##
## Makes the following new functionality available:
## - provides a method for adding a documentation source assigned to a given key to a pool of documentation
## - provides a method for adding an export for documentation to some destinations
## - automatically generation of a `README` and `FULLREADME` documentation
## - automatically adding a documentation section to the homepage

import os
import re

from anise.framework import projects
from anise.framework import features
from anise.framework import results
from anise import utils


## Describes a documentation export.
class Export:

    def __init__(self):
        pass

    def supports(self, name):
        return getattr(self, "is"+name, False)


## Describes an export of an anise documentation directly into the homepage.
class HomepageExport(Export):

    ##@param title The title of the export, also used as link label in the documentation section of the homepage.
    def __init__(self, title):
        Export.__init__(self)
        self.title = title


## Describes an export of an anise documentation into the distribution package(s).
class PackageExport(Export):

    ##@param ofile Target file path relative to the 'raw package's root.
    ##@param heading The title.
    ##@param mode Output format ('plain' or 'pdf').
    ##@param includedeveloperdoc pdf only: If the output shall include the developer documentation as well.
    def __init__(self, ofile, heading, mode, includedeveloperdoc=False):
        Export.__init__(self)
        self.ispackageexport = True # we need to make such crazy stuff since 'isinstance' seems to not work correctly in our scenario
        self.ofile = ofile
        self.heading = heading
        self.omode = mode
        self.includedeveloperdoc = includedeveloperdoc


## Describes an export of an anise documentation back into the source tree.
class SourceExport(Export):

    ##@param ofile Target file path relative to the source root.
    ##@param heading The title.
    ##@param mode Output format ('plain' or 'pdf').
    ##@param includedeveloperdoc pdf only: If the output shall include the developer documentation as well.
    def __init__(self, ofile, heading, mode, includedeveloperdoc=False):
        Export.__init__(self)
        self.issourceexport = True # we need to make such crazy stuff since 'isinstance' seems to not work correctly in our scenario
        self.ofile = ofile
        self.heading = heading
        self.omode = mode
        self.includedeveloperdoc = includedeveloperdoc


class _Pool:

    def __init__(self):
        self.list = []

    ## Adds an anise documentation.
    ##@param key The documentation key for storage (later used for referencing this text).
    ##@param src The documentation source text.
    def add(self, key, src):
        self.list.append([key, src])

class _Exports:

    def __init__(self):
        self.list = []

    ## Exports an anise documentation to some targets.
    ##@param key The documentation key name you want to export.
    ##@param outchannels A list of output channels which specify an documentation export target.
    def add(self, key, outchannels):
        self.list.append((key, outchannels))


## Configures a project for creating a Doxygen developer documentation.
def has_doxygen_developerdocumentation():
    projects.currentproject().makedeveloperdoc = tasks.makedeveloperdoc_doxygen


@features.hook(features.HOOK_BEFORE_DEFINITION, provides=["documentations"])
def _initproject():
    projects.currentproject().documentation.exports = _Exports()
    projects.currentproject().documentation.pool = _Pool()
    projects.currentproject().addhook(features.loadfeature("packages").featuremodule.HOOK_ENRICHRAWPACKAGE,
                                      lambda destdir: projects.currentproject().writedocumentations(destdir=destdir))
    projects.currentproject().writedocumentations = tasks.writedocumentations


@features.hook(features.loadfeature("releasing").featuremodule.HOOK_RELEASE, provides=["documentations", "PRE"], requires=["datainjections"])
def _compose_readmes():
    project = projects.currentproject()
    def token_in_map(t, m):
        for mk, ms in m:
            if mk == t:
                return ms
        return None
    maturity = project.getprojectstatusdescription() if hasattr(project, "getprojectstatusdescription") else ""
    readmedefaultloc = project.projectdir + "/_meta/readme.src"
    if not token_in_map("README", project.documentation.pool.list) and os.path.isfile(readmedefaultloc):
        project.documentation.pool.add("README", utils.basic.readfromfile(readmedefaultloc, onestring=True))
    if token_in_map("README", project.documentation.pool.list):
        downgraded_readme = utils.documentation.markdown_downgrade_headings(token_in_map("README", project.documentation.pool.list), 1)
        project.documentation.pool.add("_README", downgraded_readme)
        project.documentation.exports.add(key="FULLREADME", outchannels=[HomepageExport("Manual")])
    else:
        project.documentation.pool.add("_README", "\n... is currently not available :-/\n""")
    if not token_in_map("FULLREADME", project.documentation.pool.list):
        _authors = " and ".join(([", ".join(project.authors[0:-1])] if len(project.authors) > 1 else [])
                                + [project.authors[-1]])
        project.documentation.pool.add("_LONGDESCRIPTION", project.longdescription)
        project.documentation.pool.add("FULLREADME", """
# License
{projectname} is written by {authors} under the terms of the {license}.

Please read the `LICENSE` file from the package and the \\ref _dependencies "Dependencies" section for included
third-party stuff.

# About
\\copydoc _LONGDESCRIPTION

Are you currently reading from another source than the homepage? Are you in doubt if that place
is up-to-date? If yes, you should visit {thehomepage} and check that. You are currently reading
the manual for version {version}.

# Maturity
{maturity}
\\anchor _dependencies

# Dependencies
<div class='deps'>
{dependencies}
</div>

# User Documentation
\\copydoc _README
""".format(projectname=project.name, version=project.getversion(),
            dependencies=project.getdependencydocument(), thehomepage=(getattr(project, "getwebsiteurl", None) or (lambda:"the homepage"))(),
            summary=project.summary, authors=_authors, license=project.license.name, maturity=maturity))
    heading = project.name[0].upper() + project.name[1:] + " Manual"
    project.documentation.exports.add(key="FULLREADME", outchannels=[PackageExport("/README", heading, "plain")])
    project.documentation.exports.add(key="FULLREADME", outchannels=[PackageExport("/README.pdf", heading, "pdf",
                                                        includedeveloperdoc=getattr(project,
                                                                                    "readme_pdf_include_developer_doc",
                                                                                    False))])

@features.hook(features.HOOK_BEFORE_EXECUTION, requires=["documentations"])
def _add_homepage_section():
    project = projects.currentproject()

    def my_homepage_section(homepage, sourcedir, version, head4, bannerimage, *kwargs):
        documentation = "The following documentation is available:\n\n"
        isempty = True
        for (ekey, echans) in project.documentation.exports.list:
            for echan in echans:
                if type(echan) is HomepageExport:
                    isempty = False
                    os.mkdir(homepage.path+"/"+ekey)
                    utils.documentation.generate_doxygen_userdocumentation_ashtml(head1=project.name, head2=echan.title,
                                                                                  head3="based on release: " + version,
                                                                                  head4=head4,
                                                                                  sourcedir=sourcedir,
                                                                                  targetdir=homepage.path+"/"+ekey,
                                                                                  basecolor=project.basecolor,
                                                                                  bannerimage=bannerimage,
                                                                                  documentations=project.documentation.pool.list,
                                                                                  anisedatadir=project.anisedatadir)
                    documentation += "[{title}]({ekey}/{ekey}.html)\n\n".format(title=echan.title, ekey=ekey)
        if hasattr(project, "makedeveloperdoc"):
            isempty = False
            devdoc = project.makedeveloperdoc()
            devdoc.dl(to=homepage.path + "/developerdoc")
            documentation += "[Developer Documentation](developerdoc/index.html)\n\n"
        if not isempty:
            return documentation
    project.homepage.sections.add(3000, "Documentation", my_homepage_section)


@features.hook(features.HOOK_BEFORE_DEFINITION, requires=["releasing"])
def _add_release_task_for_export_to_source():
    project = projects.currentproject()
    def mytask():
        tasks.writedocumentations(project.projectdir, throw_on_existing=False, fortype="sourceexport")
    project.releasing.releasetasks.add(mytask)


class tasks:

    ##Writes the anise documentation, as specified in the project description, to the filesystem.
    ##@param destdir The destination path for writing the output to.
    ##@param throw_on_existing If already existing files are critical errors.
    @staticmethod
    def writedocumentations(destdir, throw_on_existing=True, fortype="packageexport"):
        project = projects.currentproject()

        for (ekey, echans) in project.documentation.exports.list:
            for echan in echans:
                if echan.supports(fortype):
                    fullfn = destdir+"/"+echan.ofile
                    if throw_on_existing and os.path.exists(fullfn):
                        raise utils.exceptions.BadFormatError("there already is a '{fullfn}', which is forbidden.".format(fullfn=fullfn))
                    utils.basic.mkdirs(os.path.dirname(fullfn))
                    if echan.omode == "pdf":
                        utils.documentation.generate_doxygen_userdocumentation_aspdf(head1=project.name,
                                                                                     head2=echan.heading,
                                                                                     sourcedir=project.projectdir,
                                                                                     targetfile=fullfn,
                                                                                     documentations=project.documentation.pool.list,
                                                                                     targetdocumentation=ekey,
                                                                                     includedeveloperdoc=echan.includedeveloperdoc)
                    elif echan.omode == "plain":
                        utils.documentation.generate_doxygen_userdocumentation_asplaintext(projectname=project.name,
                                                                                           head=echan.heading,
                                                                                           sourcedir=project.projectdir,
                                                                                           targetfile=fullfn,
                                                                                           documentations=project.documentation.pool.list,
                                                                                           targetdocumentation=ekey)
                    else:
                        raise utils.exceptions.BadInputError("unknown document output format '{omode}'.".format(omode=echan.omode))


    ##Writes the developer documentation, as specified in the project description, and returns it as Filestructure.
    @staticmethod
    @utils.logging.log_start_stop("Creating the developer documentation")
    def makedeveloperdoc_doxygen():
        project = projects.currentproject()
        tempdir = results.TempDir(dirname=project.name + "-devdoc")
        rawpkg = project.makerawpackage(dirname=project.name)
        sourcedir = rawpkg.path
        bannerimage = project.projectdir + "/" + project.getbannerimage()
        version = project.getversion()
        maturity = project.getprojectstatusdescription() if hasattr(project, "getprojectstatusdescription") else ""
        mainpagetext = """
    /**
    \mainpage Main page

    This is a documentation for developers of {projectname} as well as interested hackers, who want
    to work with the source code. It is automatically created from the source code comments. It is
    not guaranteed that the information is correct or up-to-date (even if it is based on the latest version).
    However, it should give a good overview.

    What you see here is based on the version {version}.

    {maturity}
    */""".format(projectname = project.name, version=version, maturity=maturity)
        utils.documentation.generate_doxygen_developerdocumentation_ashtml(head1=project.name,
                                                                           head2="Developer Documentation",
                                                                           additionaltext=mainpagetext,
                                                                           sourcedir=sourcedir,
                                                                           targetdir=tempdir.path,
                                                                           basecolor=project.basecolor,
                                                                           bannerimage=bannerimage,
                                                                           documentations=project.documentation.pool.list)
        return tempdir


## Loads the content of anisedoc sources (which contain ANISEDOC tags) into the documentation store.
## @param src file or directory with anisedoc sources
def add_anisedoc_source(src):
    if os.path.isdir(src):
        for s in os.listdir(src):
            add_anisedoc_source(src + "/" + s)
    elif os.path.isfile(src):
        currentprefix = None
        currentdoc = None
        currentcontent = ""
        def end_of_doc():
            nonlocal currentdoc
            nonlocal currentcontent
            exists = False
            for entry in projects.currentproject().documentation.pool.list:
                if entry[0] == currentdoc:
                    entry[1] += currentcontent
                    exists = True
                    break
            if not exists:
                projects.currentproject().documentation.pool.add(currentdoc, currentcontent)
            currentdoc = None
            currentcontent = ""
        for line in utils.basic.readfromfile(src, onestring=False):
            if currentdoc:
                if line.startswith(currentprefix):
                    currentcontent += line[len(currentprefix):] + "\n"
                else:
                    end_of_doc()
            else:
                i = line.find("ANISEDOC ")
                if i == 0:
                    utils.logging.logwarning("skipped an ANISEDOC tag because it has a null-length prefix")
                elif i > -1:
                    currentprefix = line[0:i]
                    if not re.search("[A-Za-z0-9]", currentprefix):
                        currentdoc = line[i+9:].strip()
        if currentdoc:
            end_of_doc()

markdown_downgrade_headings = utils.documentation.markdown_downgrade_headings
