
# Copyright 2014  Malcolm Inglis <http://minglis.id.au>
#
# This file is part of Puck.
#
# Puck is free software: you can redistribute it and/or modify it under the
# terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# Puck is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for
# more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Puck. If not, see <https://gnu.org/licenses/>.


class PuckError(Exception):
    exit_code = 1


class NoPackageJsonError(PuckError):
    exit_code = 2


class MissingDependencyError(PuckError):
    exit_code = 3


class DependencyConflictError(PuckError):
    exit_code = 4


class RepoVerificationError(PuckError):
    exit_code = 5


class DuplicatePathError(PuckError):
    exit_code = 6


class FailedRepoCloneError(PuckError):
    exit_code = 7


