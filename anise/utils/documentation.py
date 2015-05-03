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

##@package anise.utils.documentation
##Documentation generation
import os
import math
import re
import shlex
import shutil

import anise.utils.basic

from anise.utils import exceptions
from anise.framework import results


## Internally used for scaling a color tuple to a new one with the same hue but a given brightness.
def _scalecolor(c, avg):
    r = c[0]
    g = c[1]
    b = c[2]
    myavg = (r + g + b) / 3
    if myavg < avg:
        _missingR = 1.0 - r
        _missingG = 1.0 - g
        _missingB = 1.0 - b
        _mavg = (_missingR + _missingG + _missingB) / 3
        _missingR *= ((1 - avg) / _mavg)
        _missingG *= ((1 - avg) / _mavg)
        _missingB *= ((1 - avg) / _mavg)
        return [1 - _missingR, 1 - _missingG, 1 - _missingB]
    else:
        f = avg / myavg
        return [r * f, g * f, b * f]


## Internally used for computing some css colors for the given basecolor (with different brightnesses)
def _derivecolors(c):
    return ["rgb({0},{1},{2})".format(*[min(int(x * 255), 255) for x in _c]) for _c in [
        _scalecolor(c, 0.0), _scalecolor(c, 0.1), _scalecolor(c, 0.2), _scalecolor(c, 0.3),
        _scalecolor(c, 0.4), _scalecolor(c, 0.5), _scalecolor(c, 0.6), _scalecolor(c, 0.7),
        _scalecolor(c, 0.8), _scalecolor(c, 0.9),
    ]]


## Decreases the heading level for all headings in a Markdown document by a certain degree. This is needed for
## embedding one Markdown document in another one without breaking the section hierarchy.
def markdown_downgrade_headings(docsrc, levels):
    result = ""
    moresharps = "#" * levels
    for line in docsrc.split("\n"):
        if line.startswith("#"):
            line = moresharps + line
        result += line + "\n"
    return result[:-1]


## Writes a developer documentation as html (powered by Doxygen). You find it afterwards in `index.html`
## (and tons of other files).
## This will contain all user documentations as well, so references into it will work.
## @param head1 The first heading (typically the project name)
## @param head2 The second heading
## @param head3 The third heading (typically used for a special flavour of developer documentation)
## @param additionaltext Auxiliary source code passed to Doxygen for injecting additional content (e.g. mainpage text)
## @param sourcedir The directory where the sourcefiles are
## @param targetdir The directory for the html output
## @param basecolor The basecolor for colouring the output
## @param bannerimage Absolute path to the banner image (will be copied)
## @param documentations An anise documentations tuple for further pages, which do not exist in the sourcecode
##                       (e.g. the readme sources) as added by anise.features.documentation.add
## @param doxygensettings Additional Doxygen configuration for finetuning.
def generate_doxygen_developerdocumentation_ashtml(*, head1, head2="Developer Documentation", head3="",
                                                   additionaltext="", sourcedir, targetdir, basecolor, bannerimage=None,
                                                   documentations=[], doxygensettings=""):
    pname = (head1 + ": " + head2).replace('"', r'\"')
    generate_doxygen_documentation(head1, head2, head3, None, sourcedir, targetdir,
                                   'PROJECT_NAME="{0}"\n'.format(pname) + doxygensettings, "HTML", additionaltext,
                                   basecolor, bannerimage, [], True, "", documentations)


## Writes all user documentations as html (powered by Doxygen). You find it afterwards in the `(documentkey).html`
## files (and tons of other files).
## This will contain the developer documentation as well, so references into it will work.
## @param head1 The first heading (typically the project name)
## @param head2 The second heading
## @param head3 The third heading
## @param additionaltext Auxiliary source code passed to Doxygen for injecting additional content
## @param sourcedir The directory where the sourcefiles are
## @param targetdir The directory for the html output
## @param basecolor The basecolor for colouring the output
## @param bannerimage Absolute path to the banner image (will be copied)
## @param documentations An anise documentations tuple for further pages, which do not exist in the sourcecode
##                       (e.g. the readme sources) as added by anise.features.documentation.add
## @param doxygensettings Additional Doxygen configuration for finetuning.
def generate_doxygen_userdocumentation_ashtml(*, head1, head2, head3="", head4="", additionaltext="", sourcedir,
                                              targetdir, basecolor, bannerimage=None, documentations,
                                              anisedatadir, doxygensettings=""):
    generate_doxygen_documentation(head1, head2, head3, head4, sourcedir, targetdir, doxygensettings, "HTML",
                                   additionaltext, basecolor, bannerimage, [], False,
                                   _doxygen_additionalcss_userdocumentation, documentations,
                                   anisedatadir=anisedatadir,
                                   htmlheadertranslation=lambda x: x.replace("$title", head2),)


## Writes one user documentation page as manpage (powered by Doxygen) and returns the path to the result file.
## @param projectname The project name
## @param entityname The `NAME` for the manpage (typically the name of the command, function or whatever)
## @param section The section number (see man manpage)
## @param additionaltext Auxiliary source code passed to Doxygen for injecting additional content
## @param sourcedir The directory where the sourcefiles are
## @param targetdir The directory for the manpage output
## @param documentations An anise documentations tuple for further pages, which do not exist in the sourcecode
##                       (e.g. the readme sources) as added by anise.features.documentation.add
## @param targetdocumentation The key for the documentation which must be written
## @param doxygensettings Additional Doxygen configuration for finetuning.
def generate_doxygen_userdocumentation_asmanpage(*, projectname, entityname, section, additionaltext="", sourcedir,
                                                 targetdir, documentations, targetdocumentation, doxygensettings=""):
    entityname = entityname.replace(" ", "-")
    _itext = """/*!
    \\page {entityname}
    \\copydoc {targetdocumentation}
    */
    """.format(**locals())
    generate_doxygen_documentation(projectname, None, None, None, sourcedir, targetdir,
                                   'MAN_EXTENSION=".{0}"\n'.format(section)+doxygensettings, "MAN",
                                   additionaltext + "\n" + _itext, (0,0,7), None, [], False, "", documentations)
    return "{targetdir}/man/man{section}/{entityname}.{section}".format(**locals())


## Writes one user documentation page as plain text (powered by Doxygen).
## @param projectname The project name
## @param head The heading
## @param additionaltext Auxiliary source code passed to Doxygen for injecting additional content
## @param sourcedir The directory where the sourcefiles are
## @param targetfile The target file for the plaintext output
## @param documentations An anise documentations tuple for further pages, which do not exist in the sourcecode
##                       (e.g. the readme sources) as added by anise.features.documentation.add
## @param targetdocumentation The key for the documentation which must be written
## @param doxygensettings Additional Doxygen configuration for finetuning.
def generate_doxygen_userdocumentation_asplaintext(*, projectname, head, additionaltext="", sourcedir, targetfile,
                                                   documentations, targetdocumentation, doxygensettings=""):
    with results.TempDir() as tempdir:
        f = generate_doxygen_userdocumentation_asmanpage(projectname=projectname, entityname=head,
                                                         section=7,
                                                         additionaltext=additionaltext, sourcedir=sourcedir,
                                                         targetdir=tempdir.path, documentations=documentations,
                                                         targetdocumentation=targetdocumentation,
                                                         doxygensettings=doxygensettings)
        plaintext = anise.utils.basic.call("man -l {0} | col -b".format(shlex.quote(f)), shell=True,
                                           raise_on_errors="Problem while unformatting man page")
        res = ["  " + projectname + ": " + head]
        res.append("-" * len(res[0]) + "\n")
        began = None
        for l in plaintext[1].split("\n"):
            if began is not None and began >= 0:
                res.append(l)
            elif began is None and l.startswith("NAME"):
                began = -1
            elif began is not None:
                began += 1
    anise.utils.basic.writetofile(targetfile, "\n".join(res[:-1]))


## Writes one user documentation page as pdf (powered by Doxygen).
## @param head1 The first heading (typically the project name)
## @param head2 The second heading
## @param additionaltext Auxiliary source code passed to Doxygen for injecting additional content
## @param sourcedir The directory where the sourcefiles are
## @param targetfile The target file for the pdf output
## @param documentations An anise documentations tuple for further pages, which do not exist in the sourcecode
##                       (e.g. the readme sources) as added by anise.features.documentation.add
## @param targetdocumentation The key for the documentation which must be written
## @param doxygensettings Additional Doxygen configuration for finetuning.
## @param includedeveloperdoc If the pdf shall include the developer documentation.
def generate_doxygen_userdocumentation_aspdf(*, head1, head2, additionaltext="", sourcedir, targetfile, documentations,
                                             targetdocumentation, doxygensettings="", includedeveloperdoc=False):
    with results.TempDir() as tempdir:
        generate_doxygen_documentation(head1, head2, None, None, sourcedir, tempdir.path,
                                       "LATEX_BATCHMODE=YES\n" + doxygensettings, "LATEX", additionaltext, (0,0,7),
                                       None, [], False, "", documentations)
        refmantex = anise.utils.basic.readfromfile(tempdir.path + "/latex/refman.tex", onestring=False)
        refmantexnew = []
        intitlepage = False
        for l in refmantex:
            if intitlepage:
                if l.startswith("\\end{titlepage"):
                    intitlepage = False
                continue
            elif l.startswith("\\begin{titlepage"):
                intitlepage = True
                continue
            elif l.startswith("\\chapter{"):
                if not includedeveloperdoc or (l[9:l.find("}")] not in ["Namespace Index", "Hierarchical Index",
                                                                        "Class Index", "Namespace Documentation",
                                                                        "Class Documentation"]):
                    chapteraccepted = False
                    continue
                chapteraccepted = True
            elif l.startswith("\\input{"):
                if l.find("{" + targetdocumentation + "}") > -1:
                    refmantexnew.append(
                        "\\chapter{" + head2 + "}\n\\label{" + head2 + "}\n\\hypertarget{" + targetdocumentation +
                        "}{}\n\\input{" + targetdocumentation + "}\n")
                elif chapteraccepted:
                    refmantexnew.append(l)
                else:
                    continue
            elif l.startswith("\\label{"):
                continue
            elif l.startswith("\\hypertarget{"):
                continue
            else:
                refmantexnew.append(l)
        anise.utils.basic.writetofile(tempdir.path + "/latex/refman.tex", "".join(refmantexnew))
        tex = anise.utils.basic.readfromfile(tempdir.path + "/latex/" + targetdocumentation + ".tex", onestring=False)
        texstring = "".join(tex)
        texnew = []
        for l in tex:
            ll = ""
            iend = 0
            if not includedeveloperdoc:
                for linkmatch in re.finditer(r"\\hyperlink\{([^{}]+)\}\{([^{}]+)\}", l):
                    starthl = linkmatch.start(0)
                    endhl = linkmatch.end(0)
                    linktgt = linkmatch.group(1)
                    linklbl = linkmatch.group(2)
                    exists = texstring.find("\\hypertarget{"+linktgt+"}") > -1
                    if exists:
                        ll += l[iend:endhl]
                    else:
                        ll += l[iend:starthl] + linklbl
                    iend = endhl
                l = ll + l[iend:]
            if re.match("^\\\\[a-z]*section\\*\\{", l):
                ast = l.find("*")
                texnew.append(l[0:ast] + l[ast + 1:])
            else:
                texnew.append(l)
        anise.utils.basic.writetofile(tempdir.path + "/latex/" + targetdocumentation + ".tex", "".join(texnew))
        with anise.utils.basic.ChDir(tempdir.path + "/latex"):
            anise.utils.basic.call("make", "refman.pdf")
        tempdir.dl(subpath="latex/refman.pdf", to=targetfile)


## Writes the project homepage (powered by Doxygen). You find it afterwards in `index.html`
## (and tons of other files).
## @param head1 The first heading (typically the project name)
## @param head2 The second heading (typically a one-liner description)
## @param head3 The third heading (typically version information)
## @param sourcedir The directory where the sourcefiles are
## @param targetdir The directory for the html output
## @param basecolor The basecolor for colouring the output
## @param bannerimage Absolute path to the banner image (will be copied)
## @param sections A list of (sectiontitle,sectionsource) tuples for the actual content.
## @param anisedatadir Absolute path to the anise data dir (needed for finding icons, ...; typically somewhere
##                     in the anise installation path)
## @param doxygensettings Additional Doxygen configuration for finetuning.
def generate_doxygen_homepage(*, head1, head2, head3, head4, sourcedir, targetdir, basecolor, bannerimage, sections,
                              anisedatadir, doxygensettings=""):
    page = "/*!\n\\mainpage " + head1 + "\n"
    headlinks = []
    for section, sectiontext in sections:
        sectionanchor = "".join([x for x in section.lower() if x in "abcdefghijklmnopqrstuvwxyz0123456789"])
        page += "\\anchor {sectionanchor}\n# {section} #\n{sectiontext}\n".format(**locals())
        headlinks.append((section, "#" + sectionanchor))
    page += "*/"
    generate_doxygen_documentation(head1, head2, head3, head4, sourcedir, targetdir,
                                   "PROJECT_NAME=\n" + doxygensettings,
                                   "HTML", page, basecolor,
                                   bannerimage, headlinks, False, _doxygen_additionalcss_homepage, [],
                                   anisedatadir=anisedatadir)
    return targetdir


## Writes some output with Doxygen. Mostly used by some higher-level functions in this module.
## @param head1 The first heading
## @param head2 The second heading
## @param head3 The third heading
## @param head4 The fourth heading
## @param sourcedir The directory where the sourcefiles are
## @param targetdir The directory for the output
## @param doxygensettings Additional Doxygen configuration for finetuning.
## @param outputformat The desired output format (as in doxygen config's GENERATE_xxx keys)
## @param additionalsources Auxiliary source code passed to Doxygen for injecting additional content
## @param basecolor The basecolor for colouring the output
## @param bannerimage Absolute path to the banner image (will be copied)
## @param headlinks Links in the heading panel (html output only)
## @param showdoxygennavbar If the doxygen navigation bar should be visible
## @param css Additional css (html output only)
## @param documentations An anise documentations tuple for further pages, which do not exist in the sourcecode
##                       (e.g. the readme sources) as added by anise.features.documentation.add
## @param anisedatadir Absolute path to the anise data dir (needed for finding icons, ...; typically somewhere
##                     in the anise installation path)
## @param htmlheadertranslation A function which can replace stuff in the default html header (html output only)
def generate_doxygen_documentation(head1, head2, head3, head4, sourcedir, targetdir, doxygensettings, outputformat,
                                   additionalsources, basecolor, bannerimage, headlinks, showdoxygennavbar,
                                   css, documentations, anisedatadir=None, htmlheadertranslation=None):
    imagepath = anisedatadir if anisedatadir else ""
    if bannerimage:
        shutil.copyfile(bannerimage, targetdir + "/banner.png")
        bannerimage = "banner.png"
    if not head2:
        head2 = ""
    if not head3:
        head3 = ""
    if not head4:
        head4 = ""
    col00, col01, col02, col03, col04, col05, col06, col07, col08, col09 = _derivecolors(basecolor)
    _lb = "{"
    _rb = "}"
    additionalcss = (_doxygen_additionalcss + css).replace("}", "##LB_##").replace("{", "{_lb}")\
                        .replace("##LB_##", "{_rb}").replace(">", "}").replace("<", "{").format(**locals()) + "\n"
    if not showdoxygennavbar:
        additionalcss += """\n#navrow1, #navrow2, #navrow3, #navrow4, #navrow5, #navrow6, #navrow7, #navrow8, #navrow9 {
        visibility: collapse;}\n"""

    r, g, b = (x * 255 for x in basecolor)
    colorhue = int(math.atan2(1.732050808 * (g - b), (2 * r - g - b)) * 57.295779513) % 360
    hheadlinks = "".join(
        ["<a class='sectionlink indexlevel1 indexlevel2' href='{src}'>{name}</a>"
        .format(name=x[0], src=x[1]) for x in headlinks
        ]) if headlinks else ""
    bannerimg = "<img id='bannerimage' src='{0}'/>".format(bannerimage) if bannerimage else ""
    htmlheader = _doxygen_htmlheader
    if htmlheadertranslation:
        htmlheader = htmlheadertranslation(htmlheader)
    htmlheader = htmlheader.format(**locals())

    for dockey, docsrc in documentations:
        additionalsources += "\n/*!\n\\page " + dockey + "\n" + docsrc + "\n*/\n"

    uoformat = outputformat.upper()
    with results.TempDir() as tempdir:
        tpath = tempdir.path
        anise.utils.basic.writetofile(tpath + "/_anise_additionalstuff.cpp", additionalsources)
        anise.utils.basic.writetofile(tpath + "/_anise_htmlheader", htmlheader)
        anise.utils.basic.writetofile(tpath + "/_anise_htmlfooter", _doxygen_htmlfooter)
        anise.utils.basic.writetofile(tpath + "/_anise_additionalcss.css", additionalcss)
        anise.utils.basic.writetofile(tpath + "/cfg",
                                      _doxygen_baseconfig.format(**locals()) + "\n" + doxygensettings)
        anise.utils.basic.call("doxygen", tpath + "/cfg", raise_on_errors="unable to generate content via doxygen")


_doxygen_baseconfig = """# Doxyfile 1.8.5
DOXYFILE_ENCODING      = UTF-8
PROJECT_NAME           = "{head1}"
PROJECT_BRIEF          = ""
OUTPUT_DIRECTORY       = "{targetdir}"
EXTRACT_ALL            = YES
#JAVADOC_AUTOBRIEF      = YES
INLINE_INHERITED_MEMB  = YES
INHERIT_DOCS           = YES
FULL_PATH_NAMES        = YES
STRIP_FROM_PATH        = {sourcedir}
EXTRACT_PRIVATE        = YES
EXTRACT_PACKAGE        = YES
EXTRACT_STATIC         = YES
EXTRACT_LOCAL_CLASSES  = YES
EXTRACT_LOCAL_METHODS  = YES
EXTRACT_ANON_NSPACES   = YES
OPTIMIZE_OUTPUT_JAVA   = YES
ENABLED_SECTIONS       =
INPUT                  = {sourcedir} {tpath}/_anise_additionalstuff.cpp
INPUT_ENCODING         = UTF-8
FILE_PATTERNS          =
RECURSIVE              = YES
HTML_OUTPUT            = .
HTML_FILE_EXTENSION    = .html
GENERATE_DOCSET        = NO
GENERATE_HTMLHELP      = NO
GENERATE_HTML          = NO
GENERATE_CHI           = NO
GENERATE_QHP           = NO
GENERATE_ECLIPSEHELP   = NO
GENERATE_TREEVIEW      = NO
GENERATE_LATEX         = NO
GENERATE_RTF           = NO
GENERATE_MAN           = NO
GENERATE_XML           = NO
GENERATE_DOCBOOK       = NO
GENERATE_{uoformat}    = YES
HAVE_DOT               = NO
HTML_HEADER            = {tpath}/_anise_htmlheader
HTML_FOOTER            = {tpath}/_anise_htmlfooter
HTML_EXTRA_STYLESHEET  = {tpath}/_anise_additionalcss.css
HTML_COLORSTYLE_HUE    = {colorhue}
HTML_COLORSTYLE_GAMMA  = 120
IMAGE_PATH             = {imagepath}
"""

_doxygen_htmlheader = """
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
        <!--BEGIN PROJECT_NAME--><title>$projectname: $title</title><!--END PROJECT_NAME-->
        <!--BEGIN !PROJECT_NAME--><title>$title</title><!--END !PROJECT_NAME-->
        <link href="$relpath^tabs.css" rel="stylesheet" type="text/css"/>
        <script type="text/javascript" src="$relpath^jquery.js"></script>
        <script type="text/javascript" src="$relpath^dynsections.js"></script>
        $treeview
        $search
        $mathjax
        <link href="$relpath^$stylesheet" rel="stylesheet" type="text/css" />
        $extrastylesheet
    </head>
    <body>
        <a name="top"></a>
        <div id="body1">
            <div id="body2">
                <div class='barepart'></div>
                <div class="tunnel">
                    <div class="tunnelinner">
                        <h1>{head1}</h1>
                        <div class='paragraph'>
                            <span class='textspan larger'>
                                {head2}
                            </span>
                        </div>
                        <div class='paragraph'>{head3}</div>
                        <div class='textspan smaller'>{head4}</div>
                        <div class='index'>
                            {hheadlinks}
                        </div>
                    </div>
                    {bannerimg}
                </div>
                <div class="tunnelshadow">
                </div>
                <div>
"""

_doxygen_htmlfooter = """
                <!-- </div> -->
                <div id="elevator">
                    <a href="#top" title="jump to top">&#x2912;</a>
                </div>
                <div>&nbsp;</div>
            </div>
        </div>
        <!--BEGIN GENERATE_TREEVIEW-->
        <div id="nav-path" class="navpath" style="visibility:collapse; height: 0;" >
        </div>
        <!--END GENERATE_TREEVIEW-->
        <!--BEGIN !GENERATE_TREEVIEW-->
        <!--END !GENERATE_TREEVIEW-->
    </body>
</html>
"""

_doxygen_additionalcss_userdocumentation = """
div.header {
    visibility: collapse;
    height: 0;
}
div.contents {
    margin-left: 40pt;
    margin-right: 40pt;
}
body, table, div, p, dl {
    font: 400 1em/1.2em sans-serif;
}
"""

_doxygen_additionalcss_homepage = """
div.downloadgroup {
    margin-left:20pt;
}
div.downloadgroup h4 {
    padding: 0;
    margin: 30pt 0 10pt -10pt;
    text-shadow: none;
}
div.downloadgroup h5, h6 {
    padding: 0;
    margin: 0;
    text-shadow: none;
    font-weight: inherit;
}
div.downloadgroup h5 {
    font-size: 0.8em;
    font-weight: 100;
    color: <col02>;
}
div.downloadgroup.download h6 {
    font-size: 1.2em;
    font-weight: 100;
    padding-left: 40pt;
    padding-top: 10pt;
}
div.downloadgroup h6 {
    font-size: 1.4em;
    font-weight: 100;
    padding-left: 20pt;
    padding-bottom: 10pt;
}
div.downloadgroup a {
    font-size: 1.5em;
    margin: 5pt;
}
div.header {
    visibility: collapse;
    height: 0;
}
div.contents {
    margin-left: 40pt;
    margin-right: 40pt;
}
body, table, div, p, dl {
    font: 400 1em/1.5em sans-serif;
}
"""

_doxygen_additionalcss = """
pre.fragment {
    border: none;
    background: rgba(255, 255, 255, 0.3);
    margin-left: 40pt;
    margin-right: 25pt;
    font-size: 0.8em;
}
div.deps div.image {
    text-align: inherit;
    float: left;
}
div.deps div.image img {
    opacity: 0.5;
    margin-right: 10pt;
}
div.image img {
    max-width: 80%;
}
div.image div.caption {
    font-weight: normal;
    padding-bottom: 20pt;
}
div.tunnel div.tunnelinner *
{
    font-weight: 100;
}
div.tunnel div.tunnelinner h1
{
    font-weight: 400;
}
body, table, div, p, dl {
    font: 400 1em/1.2em sans-serif;
}
body{
    background:<col07>;
    font-size: 1.0em;
    font-weight: 400;
    font-family: sans-serif;
}
div{
    font-size: 1.0em;
    font-weight: 400;
    font-family: sans-serif;
}
div.header{
    background: none;
    border-bottom: none;
}
div.fragment {
    background-color: rgba(255,255,255,0.5);
}
.directory tr.even {
    background: none;
}
.mdescLeft, .mdescRight, .memItemLeft, .memItemRight, .memTemplItemLeft, .memTemplItemRight, .memTemplParams {
    background: none;
}
td.memSeparator {
    border-bottom: none;
    padding-bottom: 3pt;
}
.memdoc, .memproto {
    background: none;
    border: 0 solid black;
    box-shadow: none;
}
.memproto .memname {
    font-weight: normal;
    font-size: 1.2em;
}
.memproto .memname .paramtype, .memproto .memname .paramname {
    font-weight: 100;
}
.memitem .memproto {
    padding: 20pt 20pt 0 20pt;
}
.memdoc .params .paramname {
    font-weight: 100;
    font-size: 1.1em;
}
.memitem {
    padding-bottom: 30pt;
}
.memitem .memdoc {
    padding-top: 0;
    padding-left: 70pt;
    padding-right: 20pt;
}
.memitem .memproto td.mlabels-left {
    width: auto;
}
.contents h2.groupheader {
    border-bottom: none;
    padding-bottom: 20pt;
}
dl.reflist dd {
    background: rgba(255, 255, 255, 0.20);
}
dl.reflist dt {
    background: rgba(255, 255, 255, 0.30);
}
.directory td.entry {
    padding-bottom: 6pt;
}
.directory td.desc {
    border-left: none;
}
#body1{
    background: linear-gradient(0deg,<col06>,<col09>);
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
}
#body2{
    background: url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAC8AAAAoCAYAAABuIqMUAAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAAsTAAALEwEAmpwYAAAAB3RJTUUH3gUKDTAiQUNcrwAAAB1pVFh0Q29tbWVudAAAAAAAQ3JlYXRlZCB3aXRoIEdJTVBkLmUHAAAEtklEQVRYw9WZ23LjNhBEBxdL2a/I/39hYonA7EMAV+tsQ7WufQqrWDRNEWjMpacxLJn5d0TUdfaIKPHfMSNiRMRzXUP+/1jnMyJyvXOPiB/rvEXExxrvWr97RMQ/6/yU9z7W728Lwz7aetbk/7nGmxExuzzcoMv6Ucp9W9eyXkyZfK7nt4j4a50bzAa/50gxxBCDfayzYuwAjhSspa+XFWTIfciq63qe69qWNTeIDfi+TgW/JxzirSaLvonXxzKI4ijAlxFRuwGrL4SEVNVVI7yKhIlasovFhjxLseJd3lNvToNFPfD1wl7NFNeFrLQgtLoA3+AZglzw9lwHeHq/GmOmCdnoxkUTccY8UMt3gK+HkNN7gtfYZnzTQGrkF8tPuSasNwC+mmTu8rc7ilh+wuMX5i0AznlT3R8Sl0NW2sxA6uoi93eEQMCrHV5QwJfcV4Ac4qWmpKKTDfC70pm6NSW2myThDf8vhsUK2OsScMOEiHooZNwWMvEUsMrFRQZjvFcBreCV1hom3mMrAei4ifk0DyrGrRqnCSpkIleESRfgd0lYVx80NCvyYqIepDnJYF/g0xSDMJzfJEy6JGiXAQOgCty+x5mSuFobiuSde1fxZYdrHOhqQNNjU/JDLTZNYSODNFAu+d0dX2xTQFtOJvziMrBBGPGWJuzCsIhKDy62ucq677spIs2wS0FSDbwzTIKlkR7FJKcyTjHSRBfyUvS6AT4PFkxYbEoyaeWbcT4qEnYuoTZZ+iUsq9w3qsowYaEhlOD/Ku5VQPOwWFZM/v5CdZ+wMC1f1fK0MtlHAQ0Drh0SleArwmWiMMWBngPzTS1SIYNcRo4m7geKl3ojD0xRDCjnqUASkwkvGat16IuBzUAxIUBgFdZkFZ6m4NRDIQyj6clIe+8wa/yPjy6W404mYIECymOin8Km/UHYVHP/pWY7dkxbY8SbxCHLfDdhlQhcwpaDHKiUIh2gpolzStJqBqMl64Eq6amKJCxSqdPk0IshuykwA9o+zU6piiSuWPzvFqlm+L0IeeTB618SosPVQ061fH+jLutBf/+uPChguiL0XRANtkixil5GEKVRgt3snL4jzCY8TwPQiy/Vv5tJEkKpmbBqZlPdvyGJr4PRqHGI40Uu9ze7fbd6128p0ETljYwNiXU11O5nslCyOL7I9G7CIs0iEgO2NZH2IofZBlJeJATZkM7BUxL1HY5UPa/umgcNrxw8ZcIHBm94p0lIqBEe0jm+oKnysKNi6GZfg4SJrzCNHsbzE8nWzH52iJUnwF/GYPXQ+ijcubmK6rph1NoqlZXbtQ/UTDNrW/nTdMlYQ1zTSTtswS6xMoYbyLXdSHkKvELOPuXDhFr0Q1iNodretfuKaerkoWGqhYYdrkto88ReA3vWir5/olY006x9abRWgK+I41OzSBukRSzoaFbvL2GVarZ8CXquJlSDlne98WGUZAG9TeONNAw2wekE3817Ljqm28OmoSYmahOLP/BZh4tSkfXEs4fuRZFPmkPvvlH98s3I7R1pOf0aeAkIJp72IB84n7LozUQ3A7YeDJn7ayCTJ02CsBv2lDOFbhs2GvyU+e+6fqK1Uox4awaHLmD+BLK0xQ1K/U4WAAAAAElFTkSuQmCC);
    background-size: 80%;
}
#bannerimage{
    position: absolute;
    top: 0;
    left: 0;
    min-width: 100%;
    min-height: 100%;
    z-index: 1;
}
.tunnel .index br{
    display: none;
}
.tunnel a.sectionlink{
    display: inline;
    padding: 5pt;
    margin-left: 10pt;
    background: <col06>;
    color: <col02>;
    text-decoration: none;
    text-shadow: none;
    border: none;
}
.tunnel a.sectionlink:hover{
    background: <col08>;
    color: <col04>;
    text-shadow: none;
}
.index{
    margin-bottom: 1em;
}
.tunnel .index{
    line-height: 2.2em;
    margin-bottom: 0;
}
div.barepart{
    padding: 30pt;
}
div.paragraph{
    padding: 0.3em 0 0.3em 0;
}
div.group{
    background: rgba(100,100,100,0.15);
}
div.gallery{
    padding: 2em;
    position: relative;
}
div.gallery img.gallery {
    max-width: 80%;
    max-height: 300pt;
    border: 2pt dotted <col04>;
}
div.linkgroup, div.documentation {
    margin: 8pt;
    padding: 4pt;
    font-size: 1.1em;
    border-left: 3pt solid <col02>;
}
div.linkgroup a{
    margin-left: 10pt;
    font-size: 1.2em;
}
a{
    text-decoration: none;
    color: <col02>;
    border-bottom: 1pt dotted <col03>;
    text-shadow: 0pt 0pt 5pt white;
}
a:hover{
    text-decoration: none;
    color: <col09>;
    border-bottom: 1pt dotted <col09>;
    text-shadow: 0pt 0pt 5pt black;
}
.headertitle .title {
    margin: 1.3em 0 1em 0;
    font-weight: normal;
    letter-spacing: 0.1em;
    padding-left: 30pt;
    font-size: 2.3em;
    margin: 2.5em 0 1.5em 0;
    text-shadow: 0pt 0pt 16pt <col00>;
}
h1, h2, h3, h4, h5, h6{
    margin: 1.3em 0 1em 0;
    font-weight: normal;
    letter-spacing: 0.1em;
    padding-left: 30pt;
}
h1{
    font-size: 2.3em;
    margin: 2.5em 0 1.5em 0;
    text-shadow: 0pt 0pt 16pt <col00>;
}
h2{
    font-size: 2.0em;
    text-shadow: 0pt 0pt 18pt <col00>;
}
h3{
    font-size: 1.85em;
    text-shadow: 0pt 0pt 16pt <col00>;
}
h4{
    font-size: 1.6em;
    text-shadow: 0pt 0pt 14pt <col00>;
}
h5{
    font-size:1.35em;
    text-shadow: 0pt 0pt 12pt <col00>;
}
h6{
    font-size:1.2em;
    text-shadow: 0pt 0pt 10pt <col00>;
}
.hnumber{
    background: rgba(100,100,100,0.2);
    border-radius: 4pt;
}
.tunnel{
    position: relative;
    left: 0;
    right: 0;
    padding: 10pt 30pt 30pt 30pt;
    background: linear-gradient(0deg,<col02>, <col03> 70%,<col05>);
    border-top: 2pt solid <col06>;
    border-bottom: 2pt solid <col06>;
    overflow: hidden;
    text-align: right;
    font-family: sans-serif;
    font-size: 1.4em;
    color: <col08>;
    text-shadow: 0pt 0pt 18pt black;
}
.tunnel h1{
    font-weight: normal;
    letter-spacing: 6pt;
    margin: 1em 0 0.5em 0;
    text-align: center;
}

.tunnel .padding, .tunnel .number{
    display: none;
}
.tunnelshadow{
    position: relative;
    left: 0;
    right: 0;
    background: linear-gradient(0deg,rgba(0,0,0,0),rgba(0,0,0,0.3) 60%, rgba(0,0,0,0.6) );
    width: 100%;
    height: 40pt;
}
.tunnelinner{
    z-index: 10;
    position: relative;
}
.box{
    border: 1.5pt solid <col05>;
    background: rgba(150,150,150,0.1);
    border-radius: 5pt;
    margin: 10pt;
    padding: 4pt;
}
.textspan.bold{
    font-weight: bold;
}
.textspan.monospace{
    font-family: monospace;font-weight:bold;
}
.textspan.larger{
    font-size: 1.3em;
}
.textspan.smaller{
    font-size: 0.9em;
    color: <col06>;
}
.textspan.underline{
    text-decoration: underline;
}
.textspan.italic{
    font-style: italic;
}
.boxinner.info{
    background: url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADwAAAA8CAYAAAA6/NlyAAAABmJLR0QAAAAAAAD5Q7t/AAAACXBIWXMAAAsTAAALEwEAmpwYAAAAB3RJTUUH3gUMFBwGcu0U8wAAAB1pVFh0Q29tbWVudAAAAAAAQ3JlYXRlZCB3aXRoIEdJTVBkLmUHAAAAaUlEQVRo3u3YQQ4AEAwAwfLyPt0fmgZh9ixhwkUjpKcam/bJ5nXl5m83DAwMDAwMDAwsSVLTAKDz024AAAwMDPw12FzakwYGBgYGBgYGBgYGBgYGBgYGBgY+WnVMm5ecP90wMDAwsKRrW9xpBF2Kq+7MAAAAAElFTkSuQmCC);
    background-size: 50pt 50pt;
    background-repeat: no-repeat;
    padding: 6pt 6pt 6pt 50pt;
    min-height: 38pt;
}
.boxinner.warning{
    background: url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADwAAAA8CAYAAAA6/NlyAAAABmJLR0QAAAAAAAD5Q7t/AAAACXBIWXMAAAsTAAALEwEAmpwYAAAAB3RJTUUH3gUMFBszax9GFwAAAB1pVFh0Q29tbWVudAAAAAAAQ3JlYXRlZCB3aXRoIEdJTVBkLmUHAAAAgElEQVRo3u3aWwqDMBRF0aMTL45ZhdYHOAMV2qIma//eQFjkfiaRJOk2NRfc+TpxpvvX5W1tLwwMDAwMDAwMDAwMDAwMDAwMDAx83HQwn0sDD1/OHwfugQsHW+nawaOVttLAtwZ/kiw1gfde+Z1kjSSp0vzTKj1gYGBgYGBJ+lEb5GgbPlv1RLMAAAAASUVORK5CYII=);
    background-size: 50pt 50pt;
    background-repeat: no-repeat;
    padding: 6pt 6pt 6pt 50pt;
    min-height: 38pt;
}
.boxinner.question{
    background: url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADcAAAA4CAYAAABZjWCTAAAABmJLR0QAAAAAAAD5Q7t/AAAACXBIWXMAAAsTAAALEwEAmpwYAAAAB3RJTUUH3gUMFBwPCzGsVwAAAB1pVFh0Q29tbWVudAAAAAAAQ3JlYXRlZCB3aXRoIEdJTVBkLmUHAAACB0lEQVRo3u3YzWpUMRjG8Z+OtqJT20EqIiiioCi4UMGFIAguXLv24wq8BVfehpdRUbQbF35hoZUiMogWRandiFaLpUxnXJiVi56M5nQmJQ8EBs5zkvOf5M37JhTlqW2J+tmBw6EdwATGMIIuVkP7hs+hLYRnQwt3CGdwCjv7fHcFs3iJn8MEdxoXsS/BN6ziAeYHDXcUl8PSS60Z3E/ZYaNP/y00awqRg2FpL6TqcPuQbXAXcGSrwsGVVLv4MMLtDyklSX5KoTW08Q6LWEYHo5jESZzrI8aP48Og4ZbxFK8C4N/6hY+hzeEmdkX0O9CZ6wSoJ+F3jJbwOMRUlfYMKua+4G740E6f77Yjfc1BzNxsSLTr/zjej0hfdxBwU/853mik73uOqWAy0vcpR7hjkb7XucE1wvGoSot4nxvc+Ygtvot7udWWzXD+q9J0mLlk1wN1awzXI3bKGbxIOXDdcOO4gVaFbz6cxofqDmUjtQLYeIVvLuTPXi5wrVAk763wPcejuv7dOpblblyLAJvGszpjog64qxExNhXq1FqVOhWc9eeGbCO93Qyw1HANXKrw9PBws6qGlHAnIiqQNr7mCBdTFL/ZzCo9JVzMLfRSrnATEZ6VXOFGIjxrucLF9LWeK1yMelsZToErcEVFRcOmlNcMtyM8d8puWeAKXIErcAWuwBUVFeWo3xuCU7bndB2eAAAAAElFTkSuQmCC);
    background-size: 50pt 50pt;
    background-repeat: no-repeat;
    padding: 6pt 6pt 6pt 50pt;
    min-height: 38pt;
}
.boxinner.code{
    background: url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAFEAAABRCAYAAACqj0o2AAAABmJLR0QAAAAAAAD5Q7t/AAAACXBIWXMAAAsTAAALEwEAmpwYAAAAB3RJTUUH3gUMFBwV9lNVLQAAAB1pVFh0Q29tbWVudAAAAAAAQ3JlYXRlZCB3aXRoIEdJTVBkLmUHAAAFGUlEQVR42u2bzU8dVRjGfxcuFEopWqqFa8FWoFabCibaGE1NG2Osm7rRuHJljC5cuXDhQo0L/wlXJi78A4xxo6kmNtZSC6athapgRSgWLB+lLUUvLua5CSH3MufeOTP3632Ss7lzZ+acZ96P533PDBgMBoPBYDDUHFIer/Vxnt/eqwcSG6roIdUtiRiJZolmiWaJRqJZolliAotMAV3AAWAvcC+wC2jJ89+7wDKwCPytMQXMAP/VI4lNwBPAUeCeiPddA64CY8BlYK4eSOwDXgF2xjSPqq5s0g7/eRZ4oV7iWxwkPgmcMJpKz84Z4KUKm+/bwFMFklhFWuKJCtSRGeAk8CJwARgGJiqVxAzQX8Ee1AQ8rjEvMs8BNyuJxIOO588D38ga3s1z/AOgDdguLXkfsAfYD7R7WkOnEt/zkktngStAttwk9jmc+yfwCfBviB5c0JjedGw3cAgY8hjfH9VYkmUOAzfKRaKLmP4qhMAwzAHfavjGTuA4cAz4XWRejDjfoklsczh3ukqKiT6N28B5EXotCRJdsnILsFpFcq4VeFpjSmSO+lhDY4HfjzhoseubrPG5PP/52jMRC8A2NT1SEd39oAjtBFbUJPFK4mNAR8i5PcAluUlSJM5scMklhZ32iEaUUWPlsDxzXgkxMom7gH0h5zbr5lngH3V34iYxh1WCLtCPwM/AHT301gjXbAMGgGeAbl3TKbMXcole4K0iJpAtEEc/JOgpJoVeYFCe1OYpfJzTWCjWEheV0Vz7hqktOkCH5DLoya7HSOIiMA58L0vNeVVjiddrAR5S7HyQoJE8v3kNqZCY96bn+nlFGfFUgiVakwT4kNy1wcMazgNfhlkiCtwrRZSALmjWwzmyoepZj5nELDCrh3dGbtnqkDi3WkPvxngfZuZ/KcD247cpm9Y1e4BfSG6/ZW2DRvwJuKXsXkr8dCYxZy0Tig2tnhfVCTwMjJD8xtUdYBL4QVLtrvTntjhIzGWpM3Lv7iJu5IJ2Tf5iGauZm8CvSkgrMphG3ySi2DUFnAb+kHt3KHBHRZfq2etlIrFDcfqktG9jMZaYLuGGWYJ+3RUReb+EedSthOMJW2OrqpRBzb/kmJ+OOJF1Zb7ZAiSelvDd4XCtjLLe1ZjlziMi7kAE/eiVxDB8QdB3fFlkhqE/BhIbdN1BCf9mDwlpNEkSIWiEfi4ZEdYx3++5BBySy/ooASckjS5sblCkE4xB3zmQGPX1lD2yuEFl/KhYlp4cVrlXFnferDfDsL3EzJojrttThTMu4i7jsOGVJIkuPTrXeJXLrENqDPiopuY3dGyWfSSWNwi2Qn/zSKKLq94KOZ6zuAFPmXVNsir3EkBJdXx6iwD/ulzwFMErcFH3cQ87Vg5b4VVPD3RaxI0o28YqcXqA12TeIwqysyXcZy/B9mUYZmKulUcJNve97lS6xsR2gvb/UYLG56TMf1YEF7Kg3dKHxxzvNeaZuHXNNa80SZrEQtkwDO8UaSnjntblJE3KSWKcOjLKHnBOmpz1FMOrjsQ5gjZUotKklki8DXxaZLzyIk1qhcRl4LMi4pZXaeILhZR+F8ELlIPE98XApBoTS1Q5Ug7H9xHsgwyI3Kgl1gxBV/gSNYJiCdkBPEDQQO0i2Bhv08i3TbBKsGF/Q5Y3RvBVVU3B1zZoGvgoz+/vE9OLlZWEuL8OWKcO0GBkmSWaJRqJBnNnc2ezRCPRLNFgMBgMBoPBYDAYDAaDoRz4H6u6G/F+zzydAAAAAElFTkSuQmCC);
    background-size: 35pt 35pt;
    background-repeat: no-repeat;
    padding: 6pt 6pt 6pt 50pt;
    min-height: 23pt;
    font-family: monospace;
    white-space: pre;
    overflow: auto;
}
#elevator{
    position: fixed;
    bottom: 0pt;
    right: -20pt;
}
#elevator a{
    border-radius: 10pt;
    padding:5pt 20pt 20pt 5pt;
    border: 2pt solid <col05>;
    background: <col04>;
    color: <col06>;
    font-size: 2em;
    text-shadow: none;
}
#elevator a:hover{
    border: 2pt solid <col07>;
    background: <col06>;
    color: <col08>;
}
.icon{
    opacity: 0.6;
}

"""
