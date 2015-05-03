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

##@package anise.utils.logging
##Logging
import functools
import inspect

import traceback
from anise.framework import globalvars


## Log message severities.
class Severity:
    Debug = 0
    Info = 100
    Warning = 200
    Error = 300


## Logs a text message.
##@param text The log message.
##@param severity The message severity. One of the values from anise.utils.logging.Severity.
##@param printcaller Also logs the caller name.
##@param skiplevels If given, it controls the position on the call stack which is used for logging the caller name.
def logmessage(text, severity, printcaller=True, skiplevels=1):
    if severity >= Severity.Error:
        color = "91"
    elif severity >= Severity.Warning:
        color = "93"
    elif severity >= Severity.Info:
        color = "94"
    else:
        if not globalvars.logdebug:
            return
        color = "37"
    if printcaller:
        stack = inspect.stack()
        parentframe = stack[skiplevels][0]
        name = []
        module = inspect.getmodule(parentframe)
        if module:
            name.append(module.__name__)
        if 'self' in parentframe.f_locals:
            name.append(parentframe.f_locals['self'].__class__.__name__)
        codename = parentframe.f_code.co_name
        text = ".".join(name) + ": " + text
    print("\033[{color}m{text}\033[0m".format(**locals()))


## Logs a text message with debug severity.
##@param text The log message.
##@param printcaller Also logs the caller name.
##@param skiplevels If given, it controls the position on the call stack which is used for logging the caller name.
def logdebug(text, printcaller=True, skiplevels=1):
    logmessage(text, Severity.Debug, printcaller, skiplevels+1)


## Logs a text message with info severity.
##@param text The log message.
##@param printcaller Also logs the caller name.
##@param skiplevels If given, it controls the position on the call stack which is used for logging the caller name.
def loginfo(text, printcaller=True, skiplevels=1):
    logmessage(text, Severity.Info, printcaller, skiplevels+1)


## Logs a text message with warning severity.
##@param text The log message.
##@param printcaller Also logs the caller name.
##@param skiplevels If given, it controls the position on the call stack which is used for logging the caller name.
def logwarning(text, printcaller=True, skiplevels=1):
    logmessage(text, Severity.Warning, printcaller, skiplevels+1)


## Logs a text message with error severity.
##@param text The log message.
##@param printcaller Also logs the caller name.
##@param skiplevels If given, it controls the position on the call stack which is used for logging the caller name.
def logerror(text, printcaller=True, skiplevels=1):
    logmessage(text, Severity.Error, printcaller, skiplevels+1)


## Logs an exception.
##@param exception The occurred exception. This only works from within the `except`-handler of this exception.
def logexception(exception):  # if you change this signature, also change the fallback exception logger
    e_full = traceback.format_exc()
    logdebug(e_full, printcaller=False)
    logerror("Error: "+str(exception), printcaller=False)


## Function decorator for logging start and end of a function call.
def log_start_stop(description):
    def _realdecorator(func):
        @functools.wraps(func)
        def _realfunction(*args, **kwargs):
            loginfo("Begin    '"+description+"'...", printcaller=False)
            res = func(*args, **kwargs)
            loginfo("Finished '"+description+"'.", printcaller=False)
            return res
        return _realfunction
    return _realdecorator
