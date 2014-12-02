
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


from .args import parse_args
from .logger import Logger
from .package import Package


def main(name, argv, env, cwd, outfile=None, errfile=None):
    args = parse_args(name, argv)
    logger = Logger(outfile, errfile)
    try:
        package = Package.from_path(cwd, observers=[logger])
    except FileNotFoundError:
        logger.notify('missing-package-json')
        return 1
    {'update': lambda:
         package.update(verify=not args.no_verify, dev=not args.no_dev),
     'execute': lambda:
         package.execute(args.command, env=env, check=args.check,
                         me_too=args.root, dev=not args.no_dev),
     'wipe': lambda:
         package.wipe(force=args.force, dev=not args.no_dev),
    }[args.sub]()
    return 0


