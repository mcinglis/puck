

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


