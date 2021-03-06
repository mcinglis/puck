
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


import os
from argparse import ArgumentParser

from .package import Package


def parse_args(argv):
    p = make_arg_parser(os.path.basename(argv[0]))
    args = p.parse_args(argv[1:])
    if not hasattr(args, 'sub'):
        p.error('no subcommand given')
    return args


def make_arg_parser(prog):

    p = ArgumentParser(prog=prog,
            description=
                'Manages a package according to its specification in a '
                '`Package.json` file in its root directory. Dependencies are '
                'specified and managed as separate Git repositories.',
            epilog=
                'For more information, see: '
                'https://github.com/mcinglis/puck')
    p.add_argument('-n', '--no-dev', action='store_true',
            help=
                'Don\'t update dependencies of the enclosing package defined '
                'with a `"dev": true` field, signalling they are only '
                'required for development of the enclosing package.')

    subs = p.add_subparsers()

    up = subs.add_parser('update', aliases=['u'],
            description=
                'Downloads all dependencies and development dependencies of '
                'the enclosing package, and all dependencies of '
                'dependencies, into a `{}` directory in the enclosing '
                'package\'s root directory. Then, checks out the specified '
                'version (if any) of each dependency.'
                .format(Package.DEPS_DIR))
    up.set_defaults(sub='update')
    up.add_argument('-f', '--no-verify', action='store_true',
            help=
                'Do not verify (e.g. `git tag --verify`) the chosen tag for '
                'dependencies specified with a tag pattern.')

    xp = subs.add_parser('execute', aliases=['x'],
            description=
                'Performs a depth-first traversal of the dependency tree '
                'from the root package, issuing the given command to each '
                'dependency in the tree exactly once. A package\'s '
                '`Package.json` file may specify the handler for the '
                'given command via a matching member in the `"commands"` '
                'object. If no handler is specified, a message is printed '
                'and the traversal continues. See the Puck README for more '
                'details.')
    xp.set_defaults(sub='execute')
    xp.add_argument('command')
    xp.add_argument('-c', '--check', action='store_true',
            help=
                'Fail on the first command execution that returns a non-zero '
                'return code. The default behavior is to ignore subprocess '
                'errors.')
    xp.add_argument('-r', '--root', action='store_true',
            help=
                'Also execute the command for the enclosing package.')

    return p


