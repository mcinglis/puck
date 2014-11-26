

class Logger:

    def __init__(self, outfile, errfile):
        self.outfile = outfile
        self.errfile = errfile
        self.dispatch = {
            'missing-package-json':     self.log_missing_package_json,
            'load-package':             self.log_ignore,
            'execute':                  self.log_execute,
            'no-command-handler':       self.log_no_command_handler,
            'call':                     self.log_call,
            'update':                   self.log_update,
            'no-matching-tags':         self.log_no_matching_tags
        }

    def __str__(self):
        return '{}(outfile={}, errfile={})'.format(self.__class__.__name__,
                                                   self.outfile, self.errfile)

    def print_out(self, *args, **kwargs):
        print(*args, file=self.outfile, **kwargs)

    def notify(self, event, source, **kwargs):
        self.dispatch.get(event, self.log_default)(event, source, **kwargs)

    def log_default(self, event, source, **kwargs):
        self.print_out('Event `{}` from `{}`: kwargs=`{}`'
                       .format(event, str(source), kwargs))

    def log_ignore(self, event, source, **kwargs):
        pass

    def log_missing_package_json(self, event, source):
        self.print_out('No `Package.json` found in all directories up to '
                       'the home directory.')

    def log_execute(self, event, source, command):
        self.print_out('{:<12} executing command `{}`'
                       .format(source.name + ':', command))

    def log_no_command_handler(self, event, source, command):
        self.print_out('{:<12} no handler for command `{}`'
                       .format(source.name + ':', command))

    def log_call(self, event, source, command, cwd=None):
        cmd_str = ' '.join(command)
        if cwd:
            self.print_out('[{}] {}'.format(cwd, cmd_str))
        else:
            self.print_out(cmd_str)

    def log_update(self, event, source):
        self.print_out('Updating dependency {} ...'.format(source.path))

    def log_no_matching_tags(self, event, source, path, pattern):
        self.print_out(('WARNING: no matching tags in repository `{}` for '
                        'pattern `{}`.')
                       .format(path, pattern))

