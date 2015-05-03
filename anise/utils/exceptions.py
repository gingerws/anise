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

##@package anise.utils.exceptions
##Exception subclasses


## An error in the execution of anise.
class AniseError(Exception):

    def __call__(self, *args):
        return self.__class__(*(self.args + args))


## A bad value was given as some input.
class BadInputError(AniseError):
    pass


## Some input is wrongly formatted.
class BadFormatError(AniseError):
    pass


## The communication with some other component failed.
class BadCommunicationError(AniseError):
    pass


## The execution of an external process failed.
class ProcessExecutionFailedError(AniseError):
    pass


## An internal error in the anise code occurred.
class InternalError(AniseError):
    pass


## Something required is not in place.
class RequirementsMissingError(AniseError):
    pass


## An unexpected situation led to an error.
class UnexpectedSituationError(AniseError):
    pass


