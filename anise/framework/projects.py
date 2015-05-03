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

##@package anise.framework.projects
##Implementation for the anise project object.
from anise.framework.features import Hook

_currentproject = None


## Sets the current project object (used internally by anise).
def setcurrentproject(project):
    global _currentproject
    _currentproject = project


## Returns the current project object.
def currentproject():
    global _currentproject
    return _currentproject


## Implementation for project objects.
class Project:

    def __init__(self, d):
        self.append(d)
        self.hooks = []

    def append(self, d):
        for key in d:
            try:
                setattr(self, key, d[key])
            except Exception:
                pass

    def addhook(self, eventname, fct, params=None, provides=None, requires=None, prepares=None):
        if params is None:
            params = {}
        hook = Hook(eventname, (lambda *a, **b: fct(*a, **dict(list(params.items())+list(b.items())))),
                    provides or [], requires or [], prepares or [])
        self.hooks.append(hook)

    def gethooks(self, eventname):
        def makehooklist(hooks):
            res = []
            for hhook in self.hooks:
                if hhook.eventname == eventname:
                    res.append(hhook)
            return res
        def sorthooks(hooks):
            class NotPlausibleException(Exception): pass
            res = list(hooks)
            plausible = False
            while not plausible:
                try:
                    for hookidx, hook in enumerate(res):
                        for mustmets, forwarddirection in [(hook.requires, True), (hook.prepares, False)]:
                            for mustmet in mustmets:
                                for scnidx, scanline in enumerate(res[hookidx+1:]
                                              if forwarddirection else res[:hookidx]):
                                    if mustmet in scanline.provides:
                                         if forwarddirection:
                                             movefrom = hookidx + 1 + scnidx
                                             moveto = hookidx
                                         else:
                                             movefrom = hookidx
                                             moveto = scnidx
                                         res = res[:moveto] + [res[movefrom]] + res[moveto:movefrom] + res[movefrom+1:]
                                         raise NotPlausibleException()
                    plausible = True
                except NotPlausibleException:
                    pass
            return res
        return [x.function for x in sorthooks(makehooklist(eventname))]
