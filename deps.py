#!/bin/env python3


from argparse import ArgumentParser

from deps.package import Package
from deps.logger import Logger


def main(argv, cwd, outfile, errfile):
    if argv[1] in {'-h', '--help'}:
        print_help
    if argv[1] not in {'update', 'build', '-h', '--help'}:
        print_help(errfile)
    elif argv[1] in {'-h', '--help'}:
        print_help(outfile)
    else:
        package = Package.from_path(cwd, dev_deps=True,
                                    logger=Logger(outfile, errfile))
        if argv[1] == 'update':
            package.update_deps()
        elif argv[1] == 'build':
            package.build_deps()


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


if __name__ == '__main__':
    import os
    import sys
    main(sys.argv, os.getcwd(), sys.stdout, sys.stderr)


