

class Logger:
    def __init__(self, outfile, errfile):
        self.outfile = outfile
        self.errfile = errfile

    def notify(self, event, source, *args, **kwargs):
        {'updating-dep': self.log_updating_dep,
         'conflict': self.log_conflict,
         'no-matching-tags': self.log_no_matching_tags
        }[event](source, *args, **kwargs)

    def log_updating_dep(self, source):
        print('Updating dependency at {}'.format(source.full_path),
              file=self.outfile)

    def log_conflict(self, source, other):
        print('ERROR: {} conflicts with {}.'.format(source, other),
              file=self.errfile)

    def log_no_matching_tags(self, source, tag_pattern):
        print('ERROR: no matching tags in `{}` with pattern `{}`.'
                  .format(source.full_path, tag_pattern),
              file=self.errfile)


