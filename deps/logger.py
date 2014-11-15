

class Logger:

    def __init__(self, outfile, errfile):
        self.outfile = outfile
        self.errfile = errfile
        self.dispatch = {
            'dep-update':                   self.dep_update,
            'dep-update--pull-master':      self.dep_update__pull_master,
            'dep-update--clone':            self.dep_update__clone,
            'dep-update--checkout':         self.dep_update__checkout,
            'dep-update--conflict':         self.dep_update__conflict,
            'dep-update--no-matching-tags': self.dep_update__no_matching_tags,
            'dep-load-package':             self.dep_load_package,
            'dep-build--conflict':          self.dep_build__conflict,
            'package-build':                self.package_build
        }

    def print_out(self, *args, **kwargs):
        kwargs['file'] = self.outfile
        print(*args, **kwargs)

    def print_err(self, *args, **kwargs):
        kwargs['file'] = self.errfile
        print(*args, **kwargs)

    def notify(self, event, source, *args, **kwargs):
        if event in self.dispatch.keys():
            self.dispatch[event](source, *args, **kwargs)
        else:
            self.unknown_event(event, source, *args, **kwargs)

    def unknown_event(self, event, source, *args, **kwargs):
        self.print_out('Unknown event `{}` from `{}`: args=`{}`, kwargs=`{}`'
                       .format(event, source, args, kwargs))

    def dep_update(self, source):
        self.print_out('----------\nUpdating dependency from: {}'
                       .format(source.repo, source.path))

    def dep_update__pull_master(self, source):
        pass

    def dep_update__clone(self, source):
        pass

    def dep_update__checkout(self, source, checkout):
        pass

    def dep_update__conflict(self, source, other):
        self.print_out(('ERROR: `{}` and `{}` set to update to same path, '
                        'but have a different repository and/or version.')
                       .format(source, other))

    def dep_update__no_matching_tags(self, source, tag_pattern):
        self.print_out('ERROR: no matching tags for `{}` with pattern `{}`.'
                       .format(source, tag_pattern))

    def dep_load_package(self, source):
        pass

    def dep_build__conflict(self, source, other):
        self.print_out(('ERROR: have already built `{other}` but `{source}` '
                        'is configured to load from the same path, but is a '
                        'different repository and/or version.')
                       .format(source=source, other=other))

    def package_build(self, source):
        self.print_out('Building `{}`.'.format(source.path))

