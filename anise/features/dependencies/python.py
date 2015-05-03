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

##@package anise.features.dependencies.python
## Dependencies from the Python world.
##
## Makes the following new functionality available:
## - some classes containing dependency info for typical Python projects.

from anise.framework import features

_dependenciesfeature = features.loadfeature("dependencies").featuremodule

class PythonDependency(_dependenciesfeature.Dependency):

    def __init__(self, type, version, **kwargs):
        def setdefault(k, v):
            if not k in kwargs: kwargs[k] = v
        setdefault("objectname", "python-" + version)
        setdefault("displayname", "Python " + version)
        setdefault("icon", "python")
        postfix = "" if version[0] == "2" else version[0]
        setdefault("debian", ["python{0} (>= {1})".format(postfix, version)])
        _dependenciesfeature.Dependency.__init__(self, type, **kwargs)


class DjangoDependency(_dependenciesfeature.Dependency):

    def __init__(self, type, version, python2=False, **kwargs):
        def setdefault(k, v):
            if not k in kwargs: kwargs[k] = v
        setdefault("objectname", "django-" + version)
        setdefault("displayname", "Django " + version)
        setdefault("icon", "django")
        setdefault("debian", ["python{0}-django (>= {1})".format("" if python2 else "3", version)])
        _dependenciesfeature.Dependency.__init__(self, type, **kwargs)

