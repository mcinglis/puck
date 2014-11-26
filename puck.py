#!/bin/env python3


from puck.main import main


if __name__ == '__main__':
    import os
    import sys
    sys.exit(main(name    = os.path.basename(sys.argv[0]),
                  argv    = sys.argv[1:],
                  env     = dict(os.environ),
                  cwd     = '.',
                  outfile = sys.stdout,
                  errfile = sys.stderr))


