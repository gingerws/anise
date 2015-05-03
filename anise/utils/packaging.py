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

##@package anise.utils.packaging
##Package generation

import datetime
import gzip
import shlex
import shutil
import os
import math
import anise.utils.basic
from anise.utils import exceptions
from anise.framework import results


def _isdatafile(fullpath):
    return not fullpath.endswith(".py")


## Data structure for one menu entry which comes in a Python wheel package.
class PythonWheelPackageApplicationLink:

    ##@param linkname The name of the link as the user will be able to call it.
    ##@param module The name of the module which contains the entry method.
    ##@param method The name of the entry method.
    ##@param gui If the command opens a gui (instead of a terminal application).
    def __init__(self, *, linkname, module, method, gui):
        self.linkname = linkname
        self.module = module
        self.method = method
        self.gui = gui


## Builds a Python wheel package.
##@param name The package name.
##@param version The package version string.
##@param homepage The homepage url.
##@param description A short project description.
##@param long_description A longer project description.
##@param licensename The name of the project license.
##@param maturity The project maturity string (may be `None`).
##@param authors The project authors as list of string.
##@param email The contact email address.
##@param keywords Project keywords for search services.
##@param fsroot The root directory for the package content (may be damaged).
##@param applicationlinks List of packaging.PythonWheelPackageApplicationLink which this package provide.
##@param datafileacceptor An optional function which helps deciding if a file in the source folder is a data file.
def buildpythonwheelpackage(*, name, version, homepage, description, long_description, licensename, maturity,
                            authors, email, keywords, fsroot, applicationlinks, datafileacceptor=_isdatafile):
    try:
        import setuptools as _foo_test_setuptools
    except ImportError as exc:
        raise exceptions.RequirementsMissingError("'setuptools' seem to be unavailable", exc)
    if anise.utils.basic.call("wheel version", shell=True)[0] != 0:
        raise exceptions.RequirementsMissingError("'wheel' seems to be unavailable")
    setuppy = fsroot+"/setup.py"
    if os.path.exists(setuppy):
        raise exceptions.BadFormatError("There must be no setup.py in the project root.")
    sauthors = ", ".join(authors[:-1])+(" & " if (len(authors) > 1) else "")+authors[-1]
    smaturity = "'{0}',".format(maturity) if maturity else ""
    rb = "{"
    lb = "}"
    pkgdirs = [fsroot.replace("\\", "/")]
    ppkgdirs = []
    datafilestring = ""
    while len(pkgdirs) > 0:
        pkgdir = pkgdirs.pop()
        for pkgfile in os.listdir(pkgdir):
            fpkgfile = pkgdir + "/" + pkgfile
            if os.path.isdir(fpkgfile):
                pkgdirs.append(fpkgfile)
                if os.path.exists(fpkgfile + "/__init__.py"):
                    ppkgdirs.append(fpkgfile)
    for ppkgdir in ppkgdirs:
        pkgname = ppkgdir[len(fsroot)+1:].replace("/", ".")
        ddfiles = []
        for dfile in os.listdir(ppkgdir):
            fdfile = ppkgdir + "/" + dfile
            if os.path.isfile(fdfile) and datafileacceptor(fdfile):
                ddfiles.append(dfile)
        if len(ddfiles) > 0:
            gffiles = ["'" + x.replace("'", "\\'") + "'" for x in ddfiles]
            datafilestring += "'{pkgname}': [{filesstring}],\n".format(pkgname=pkgname, filesstring=",".join(gffiles))
    consolescriptsstring = ""
    guiscriptsstring = ""
    if applicationlinks:
        for applicationlink in applicationlinks:
            newscr = "'{0}={1}:{2}',\n".format(applicationlink.linkname, applicationlink.module, applicationlink.method)
            if applicationlink.gui:
                guiscriptsstring += newscr
            else:
                consolescriptsstring += newscr
    with open(setuppy, "w") as f:
        f.write("""
from setuptools import setup, find_packages
setup(
name='{name}',
version='{version}',
description='{description}',
long_description='''{long_description}''',
url='{homepage}',
author='{sauthors}',
author_email='{email}',
license='{licensename}',
classifiers=[
{smaturity}
'Programming Language :: Python :: 3.4',
],
keywords='{keywords}',
packages=find_packages(exclude=['contrib', 'docs', 'tests*', '_meta']),
#install_requires=['peppercorn'],
package_data={rb}
{datafilestring}
{lb},
entry_points={rb}
'console_scripts': [
{consolescriptsstring}
],
'gui_scripts': [
{guiscriptsstring}
],
{lb},
)
""".format(**locals()))
    with anise.utils.basic.ChDir(fsroot):
        r, o = anise.utils.basic.call("python3", "setup.py", "bdist_wheel", "--python-tag", "py3",
                                      raise_on_errors="unable to create python wheel")
        anise.utils.logging.logdebug(o)
    for f in os.listdir(fsroot+"/dist/"):
        return results.Filestructure(fsroot+"/dist/"+f)


## Data structure for one menu entry which comes in a Debian package.
class DebianPackageMenuEntry:

    ##@param name Internal menu entry name.
    ##@param title Menu entry Title.
    ##@param category Menu entry category.
    ##@param command Menu entry command.
    ##@param gui If the command opens a gui (instead of a terminal application).
    ##@param icon The path to a menu entry icon.
    def __init__(self, *, name, title, category, command, gui, icon):
        self.name = name
        self.title = title
        self.category = category
        self.command = command
        self.gui = gui
        self.icon = icon


## Builds a Debian package (.deb).
##@param name The package name.
##@param version The package version string.
##@param image A project screenshot
##@param licensename The name of the project license.
##@param authors Project authors as list of strings.
##@param email Project email adress.
##@param summary Short project description.
##@param description Longer project description.
##@param section The Debian section name.
##@param architecture The Debian architecture name.
##@param websiteurl The project homepage url.
##@param menuentries Menu entries to register.
##@param executablelinks Symlinks to executables to be created.
##@param dependencies List of dependencies.
##@param services List of services to be registered.
##@param rawpkgpath The raw source directory; can be damaged.
##@param projectfsroot The project source directory path.
##@param prerm Bash code snippet executed before the package is removed on a target machine.
##@param postinst Bash code snippted executed after the package is installed on a target machine.
def builddebpackage(*, name, version, image, licensename, authors, email, summary, description, section,
                    architecture, websiteurl, menuentries, executablelinks, dependencies, services, rawpkgpath,
                    projectfsroot, prerm="", postinst=""):
    if anise.utils.basic.call("fakeroot -v", shell=True)[0] != 0:
        raise exceptions.RequirementsMissingError("'fakeroot' seems to be unavailable")
    if anise.utils.basic.call("dpkg --version", shell=True)[0] != 0:
        raise exceptions.RequirementsMissingError("'dpkg' seems to be unavailable")
    sdescription = "\n".join([" "+x for x in description.split("\n") if x.strip() != ""])
    conffiles = []
    sdependencies = ", ".join(dependencies)
    workdir = results.TempDir().path
    iworkdir = workdir+"/pkgtemp"
    packagerootname = "{name}-{version}-{architecture}".format(**locals())
    packageroot = "{iworkdir}/fs/{packagerootname}".format(**locals())
    placedoc = packageroot+"/usr/share/doc/"+name
    placepixmaps = packageroot+"/usr/share/pixmaps"
    placedebian = packageroot+"/DEBIAN"
    os.makedirs(iworkdir)
    os.makedirs(placedoc)
    if not rawpkgpath.endswith("/"):
        rawpkgpath += "/"
    files = [rawpkgpath]
    while len(files) > 0:
        f = files.pop()
        if os.path.isdir(f):
            for x in os.listdir(f):
                files.append(f+"/"+x)
        else:
            ff = f[len(rawpkgpath)+1:]
            gg = packageroot + "/" + ff
            dd = os.path.dirname(gg)
            if not os.path.exists(dd):
                os.makedirs(dd)
            shutil.copy2(f, gg)
    if not os.path.isdir(packageroot+"/usr/bin"):
        os.makedirs(packageroot+"/usr/bin")
    for executablelink in executablelinks.keys():
        os.symlink(executablelinks[executablelink], packageroot+"/usr/bin/"+executablelink)
    with open(placedoc+"/copyright", "w") as f:
        f.write("""Format-Specification: http://svn.debian.org/wsvn/dep/web/deps/dep5.mdwn?op=file&rev=135
Upstream-Name: {name}
Source: {websiteurl}
Files: *
Copyright: {year} {authors}
License: {licensename}
"""[1:].format(name=name, websiteurl=websiteurl,
               licensename=licensename, year=datetime.datetime.now().strftime("%Y"), authors=authors))
    changelog = """
{name} {version} unstable; urgency=low

* New upstream release.
* See website for details.

-- The {name} Team <{email}>  Mon, 14 Jan 2013 13:37:00 +0000
"""[1:].format(**locals())
    cchangelog = gzip.compress(changelog.encode("utf-8"))
    with open(placedoc+"/changelog.gz", "wb") as f:
        f.write(cchangelog)
    os.makedirs(placepixmaps)
    os.makedirs(packageroot+"/usr/share/menu")
    os.makedirs(packageroot+"/usr/share/applications")
    for menuentry in menuentries:
        sdebiancategory = menuentry.category[0]
        sfreedesktopcategory = menuentry.category[1]
        ename = menuentry.name
        etitle = menuentry.title
        cmd = menuentry.command
        cmd2 = cmd.replace('"', '\\"')
        iconsrc = projectfsroot + "/" + menuentry.icon
        iconfname = "{name}.{ename}.png".format(**locals())
        shutil.copyfile(iconsrc, placepixmaps+"/"+iconfname)
        sisterminal = "false" if menuentry.gui else "true"
        sneeds = "X11" if menuentry.gui else "text"
        with open(packageroot+"/usr/share/menu/{ename}".format(ename=ename), "w") as f:
            f.write("""
?package({ename}): \\
  command="{cmd2}" \\
  needs="{sneeds}" \\
  section="{sdebiancategory}" \\
  title="{etitle}" \\
  icon="/usr/share/pixmaps/{iconfname}"
"""[1:].format(**locals()))
        with open(packageroot+"/usr/share/applications/{ename}.desktop".format(ename=ename), "w") as f:
            f.write("""
[Desktop Entry]
Name={etitle}
Exec={cmd}
Terminal={sisterminal}
Type=Application
Categories={sfreedesktopcategory};
Icon=/usr/share/pixmaps/{iconfname}
"""[1:].format(**locals()))
    os.makedirs(packageroot+"/etc/init")
    startservicescall = ""
    stopservicescall = ""
    for service in services:
        servicename = service.name
        servicecommand = service.command
        with open(packageroot+"/etc/init/{servicename}.conf".format(name=name), "w") as f:
            f.write("""
# {name} - {name} job file

description "{name} service '{servicename}'"
author "The {name} Team <{email}>"

start on runlevel [2345]

stop on runlevel [016]

exec {servicecommand}
"""[1:].format(**locals()))
        startservicescall += "service {servicename} start\n"
        stopservicescall += "service {servicename} stop &>/dev/null\n"
        conffiles.append("/etc/init/{servicename}.conf".format(**locals()))
    size = 0
    for dirpath, dirnames, filenames in os.walk(packageroot):
        for f in filenames:
            ff = dirpath+"/"+f
            if not os.path.islink(ff):
                size += os.path.getsize(ff)
    size = int(math.ceil(size/1024.))
    os.makedirs(placedebian)
    # license
    with open(placedebian+"/copyright", "w") as f:  # TODO bug 7: doesnt work (and data is shit)
        f.write("""Format-Specification: http://svn.debian.org/wsvn/dep/web/deps/dep5.mdwn?op=file&rev=135
Upstream-Name: {name}
Source: {websiteurl}

Files: *
Copyright: 1975-2010, Ulla Upstream
License: GPL-2+
""".format(**locals()))
    # prerm
    with open(placedebian+"/prerm", "w") as f:
        f.write("""
{stopservicescall}
set -e
{prerm}
"""[1:].format(**locals()))
    # postinst
    with open(placedebian+"/postinst", "w") as f:
        f.write("""
#!/bin/bash
set -e
{postinst}
{startservicescall}
if test -x /usr/bin/update-menus; then update-menus; fi
"""[1:].format(**locals()))
    # control
    with open(placedebian+"/control", "w") as f:
        f.write("""
Package: {name}
Version: {version}
Section: {section}
Priority: optional
Architecture: {architecture}
Depends: {sdependencies}
Installed-Size: {size}
Maintainer: The {name} Team <{email}>
Provides: {name}
Homepage: {websiteurl}
Description: {summary}
{sdescription}
"""[1:].format(**locals()))
    # conffiles
    with open(placedebian+"/conffiles", "w") as f:
        f.write("\n".join(conffiles))
    anise.utils.basic.call("chmod", "-R", "u+rw,g+r,g-w,o+r,o-w", packageroot)
    anise.utils.basic.call("chmod", "-R", "0755", placedebian)
    anise.utils.basic.call("chmod", "0644", placedebian+"/conffiles")
    debfilename = "{name}_{version}_{architecture}.deb".format(**locals())
    r, o = anise.utils.basic.call(["fakeroot", "dpkg", "-b", packageroot, workdir+"/"+debfilename],
                                  raise_on_errors="unable to create debian package")
    anise.utils.logging.logdebug(o)
    return results.Filestructure(workdir+"/"+debfilename)


## Builds a Firefox addon.
##@param addonsdkpath The path to the Firefox development sdk.
##@param projectroot Path to the Fifefox addon project directory.
##@param name Name of the package.
##@param version Version of the package.
def buildfirefoxaddonpackage(*, addonsdkpath, projectroot, name, version):
    if not os.path.isfile(addonsdkpath+"/bin/activate"):
        raise exceptions.BadInputError("unable to find the Firefox addon sdk in "+addonsdkpath)
    with anise.utils.basic.ChDir(addonsdkpath):
        buildcmd = "source bin/activate && cd {0} && cfx xpi".format(shlex.quote(projectroot))
        r, o = anise.utils.basic.call("bash", "-c", buildcmd,
                                      raise_on_errors="errors while creating firefox addon")
    resfile = None
    for f in os.listdir(projectroot):
        if f.endswith(".xpi"):
            if resfile:
                raise exceptions.UnexpectedSituationError("More than one .xpi file found in "+projectroot)
            else:
                resfile = f
    if resfile is None:
        raise exceptions.UnexpectedSituationError("No .xpi file found in "+projectroot)
    destresfile = "{name}-{version}.xpi".format(**locals())
    os.rename(projectroot+"/"+resfile, projectroot+"/"+destresfile)
    return results.Filestructure(projectroot+"/"+destresfile)


## Builds an Android package with Ant.
##@param projectroot The path to the Android package.
##@param name The project name.
##@param version The project version.
##@param targetname The Ant target name which shall be built.
##@param androidpath Path to the Android sdk's `android` tool.
def buildandroidpackage_with_ant(*, projectroot, name, version, targetname, androidpath):
    with anise.utils.basic.ChDir(projectroot):
        r, o = anise.utils.basic.call(androidpath, "update", "project", "-p", ".",
                                      raise_on_errors="unable to call android sdk")
        r, o = anise.utils.basic.call("ant", targetname, raise_on_errors="errors while creating android package")
    resfile = None
    for f in os.listdir(projectroot+"/bin"):
        if f.endswith(".apk") and not f.endswith("-unaligned.apk"):
            if resfile:
                raise exceptions.UnexpectedSituationError("More than one .apk file found in "+projectroot+"/bin")
            else:
                resfile = f
    if resfile is None:
        raise exceptions.UnexpectedSituationError("No .apk file found in "+projectroot+"/bin")
    destresfile = "{name}-{version}.apk".format(**locals())
    os.rename(projectroot+"/bin/"+resfile, projectroot+"/"+destresfile)
    return results.Filestructure(projectroot+"/"+destresfile)


## Data structure for one menu entry which comes in a Windows package.
class WindowsPackageMenuEntry:

    ##@param title Menu entry Title.
    ##@param command Menu entry command.
    ##@param icon The path to a menu entry icon.
    def __init__(self, *, title, command, icon=None):
        self.title = title
        self.command = command
        self.icon = icon


## Builds a Windows installer executable (.exe).
##@param name The package name.
##@param version The package version string.
##@param licensefile The path to the full text of the project's license.
##@param authors Project authors as list of strings.
##@param email Project email adress.
##@param summary Short project description.
##@param architecture The Debian architecture name.
##@param websiteurl The project homepage url.
##@param menuentries Menu entries to register.
##@param rawpkgpath The raw source directory; can be damaged.
##@param projectfsroot The project source directory path.
##@param globalscript NSIS script global part.
##@param oninitscript NSIS script which runs at initialization of the installer.
##@param oninstallscript NSIS script which runs after file copying of the installer.
def buildwindowsinstallerpackage(*, name, version, licensefile, authors, email, summary,
                                 architecture, websiteurl, menuentries,
                                 rawpkgpath, projectfsroot, projecticon=None, globalscript="", oninitscript="",
                                 oninstallscript=""):
    if anise.utils.basic.call("makensis -VERSION", shell=True)[0] != 0:
        raise exceptions.RequirementsMissingError("'makensis' seems to be unavailable")
    workdir = results.TempDir().path
    nsifile = workdir + "/_anise_installer.nsi"
    exefilename = "{name}-{version}_{architecture}.exe".format(**locals())
    exefile = workdir + "/" + exefilename
    installsection = ""
    uninstallsection = ""
    uninstallsection2 = ""
    if not rawpkgpath.endswith("/"):
        rawpkgpath += "/"
    files = [rawpkgpath]
    sizeb = 0.0
    while len(files) > 0:
        f = files.pop()
        ff = f[len(rawpkgpath)+1:]
        ff2 = ff.replace("/", "\\")
        if os.path.isdir(f):
            for x in os.listdir(f):
                files.append(f+"/"+x)
            uninstallsection2 = "RmDir \"$0\\{ff2}\"\n".format(**locals()) + uninstallsection2
        elif not os.path.islink(f):
            sizeb += os.path.getsize(f)
            reldir = os.path.dirname(ff).replace("/", "\\")
            fsl = f.replace("/", "\\")
            installsection += "SetOutPath \"$INSTDIR\\{reldir}\"\nFile \"{fsl}\"\n".format(**locals())
            uninstallsection += "Delete \"$0\\{ff2}\"\n".format(**locals())
    tmpicons = results.TempDir()
    uninstallericon = ""
    if projecticon:
        iconsrc = projectfsroot + "/" + projecticon
        iconfname = "_{name}.ico".format(**locals())
        sizeb += os.path.getsize(iconsrc)
        fsl = tmpicons.path+"/"+iconfname
        shutil.copyfile(iconsrc, fsl)
        fsl = fsl.replace("/", "\\")
        installsection += "SetOutPath \"$INSTDIR\"\nFile \"{fsl}\"\n".format(**locals())
        uninstallsection += "Delete \"$0\\{iconfname}\"\n".format(**locals())
        uninstallericon = "$INSTDIR\\" + iconfname
    for menuentry in menuentries:
        icon = ""
        if menuentry.icon:
            ename = menuentry.title
            iconsrc = projectfsroot + "/" + menuentry.icon
            iconfname = "_{name}.{ename}.ico".format(**locals())
            sizeb += os.path.getsize(iconsrc)
            fsl = tmpicons.path+"/"+iconfname
            shutil.copyfile(iconsrc, fsl)
            fsl = fsl.replace("/", "\\")
            installsection += "SetOutPath \"$INSTDIR\"\nFile \"{fsl}\"\n".format(**locals())
            uninstallsection += "Delete \"$0\\{iconfname}\"\n".format(**locals())
            icon = "$INSTDIR\\" + iconfname
        command = menuentry.command.replace("$$", "$INSTDIR").replace("/", "\\")
        title = menuentry.title
        for x in '/?<>\:*|"':
            title = title.replace(x, "_")
        installsection += "createShortCut \"$SMPROGRAMS\\{name}\\{title}.lnk\" \"{command}\" \"\" \"{icon}\"\n".format(**locals())
        uninstallsection += "delete \"$SMPROGRAMS\\{name}\\{title}.lnk\"\n".format(**locals())
    sizekb = int(math.ceil(sizeb / 1024.))
    lb = "{"
    rb = "}"
    displayversion = version
    versionmajor = version.split(".")[0]
    try:
        versionminor = version.split(".")[1]
    except Exception:
        versionminor = "0"
    anise.utils.basic.writetofile(nsifile, """
        RequestExecutionLevel admin
        InstallDir "$PROGRAMFILES\\{name}"
        LicenseData "{licensefile}"
        Name "{name}"
        Outfile "{exefilename}"
        !include "LogicLib.nsh"
        !include "StrFunc.nsh"
        ${lb}StrLoc{rb}
        page license
        page directory
        Page instfiles
        !macro VerifyUserIsAdmin
        UserInfo::GetAccountType
        pop $0
        ${lb}If{rb} $0 != "admin" ;Require admin rights on NT4+
                messageBox mb_iconstop "Administrator rights required!"
                setErrorLevel 740 ;ERROR_ELEVATION_REQUIRED
                quit
        ${lb}EndIf{rb}
        !macroend
        {globalscript}
        function .onInit
            setShellVarContext all
            !insertmacro VerifyUserIsAdmin
            {oninitscript}
        functionEnd
        section "install"
            setOutPath "$INSTDIR"
            createDirectory "$SMPROGRAMS\\{name}"
            {installsection}
            {oninstallscript}
            writeUninstaller "$INSTDIR\\uninstall.exe"
            # Registry information for add/remove programs
            WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{name}" "DisplayName" "{name} - {summary}"
            WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{name}" "UninstallString" "$INSTDIR\\uninstall.exe"
            WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{name}" "QuietUninstallString" "$INSTDIR\\uninstall.exe /S"
            WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{name}" "InstallLocation" "$INSTDIR"
            WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{name}" "DisplayIcon" "{uninstallericon}"
            WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{name}" "Publisher" "The {name} Team"
            WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{name}" "HelpLink" "{websiteurl}"
            WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{name}" "URLUpdateInfo" "{websiteurl}"
            WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{name}" "URLInfoAbout" "{websiteurl}"
            WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{name}" "DisplayVersion" "{displayversion}"
            WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{name}" "VersionMajor" {versionmajor}
            WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{name}" "VersionMinor" {versionminor}
            WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{name}" "NoModify" 1
            WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{name}" "NoRepair" 1
            WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{name}" "EstimatedSize" {sizekb}
        sectionEnd
        function un.onInit
            SetShellVarContext all
            MessageBox MB_OKCANCEL "Permanantly remove {name}?" IDOK next
                Abort
            next:
            !insertmacro VerifyUserIsAdmin
        functionEnd
        section "uninstall"
            ReadRegStr $0 HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{name}" InstallLocation
            {uninstallsection}
            {uninstallsection2}
            rmDir "$SMPROGRAMS\\{name}"
            delete "$0\\uninstall.exe"
            rmDir "$0"
            DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{name}"
        sectionEnd
    """.format(**locals()))

    r, o = anise.utils.basic.call(["makensis", nsifile],
                                  raise_on_errors="unable to create windows installer package")
    anise.utils.logging.logdebug(o)
    tmpicons.delete()
    return results.Filestructure(exefile)
