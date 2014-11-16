#!/bin/env python3


from deps.package import Package
from deps.logger import Logger


HELP_STR = '''
usage: deps [-h | update | COMMAND]

Manages dependencies between Git projects, as specified by a `Package.json`
file in the root directory of the project. `deps` may be executed in any
subdirectory of the package. `COMMAND` must be one of:

    update              updates the dependencies of the package; either clones
                        or pulls from the specified repository locations, then
                        checks out the specified version (if any).

    build               builds the dependencies of the package, and their
                        dependendencies, in the required order (i.e. building
                        sub-dependencies before dependencies). You should run
                        `deps update` before building.

For more information, read the deps README.
<https://github.com/mcinglis/deps>
'''

def print_help(to):
    print(HELP_STR.strip(), file=to)


def main(argv, cwd, outfile, errfile):
    if argv[1] in {'-h', '--help'}:
        print_help(outfile)
    else:
        package = Package.from_path(cwd, logger=Logger(outfile, errfile))
        if argv[1] == 'update':
            package.update_deps(dev=True)
        for command in argv[1:]:
            package.execute(command)


if __name__ == '__main__':
    import os
    import sys
    main(sys.argv, os.getcwd(), sys.stdout, sys.stderr)


