

from .package import Package
from .logger import Logger
from .args import parse_args


def main(name, argv, env, cwd, outfile, errfile):
    args = parse_args(name, argv)
    logger = Logger(outfile, errfile)
    try:
        package = Package.from_path(cwd, observer=logger)
    except FileNotFoundError:
        logger.notify(event='missing-package-json', source=None)
        return 1
    {'update': lambda:
         package.update(dev=not args.no_dev, verify=not args.no_verify),
     'execute': lambda:
         package.execute(args.command, env=env, check=args.check,
                         dev=not args.no_dev, me_too=args.root),
     'wipe': lambda:
         package.wipe(dev=not args.no_dev, force=args.force),
    }[args.sub]()
    return 0


