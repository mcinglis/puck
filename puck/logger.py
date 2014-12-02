
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


class Logger:

    def __init__(self, outfile, errfile):
        self.outfile = outfile
        self.errfile = errfile
        self.dispatch = {
            'missing-package-json': self.log_missing_package_json,
            'execute':              self.log_execute,
            'no-command-handler':   self.log_no_command_handler,
            'call':                 self.log_call,
            'update':               self.log_update,
            'no-matching-tags':     self.log_no_matching_tags,
            'missing-dep':          self.log_missing_dep
        }

    def __str__(self):
        return '{}(outfile={}, errfile={})'.format(self.__class__.__name__,
                                                   self.outfile, self.errfile)

    def out(self, *args, **kwargs):
        if self.outfile:
            print(*args, file=self.outfile, **kwargs)

    def err(self, *args, **kwargs):
        if self.errfile:
            print(*args, file=self.errfile, **kwargs)

    def notify(self, event, **kwargs):
        self.dispatch.get(event, self.log_default)(event, **kwargs)

    def log_default(self, event, **kwargs):
        self.err('WARNING: event `{}` received: kwargs={}'
                   .format(event, kwargs))

    def log_missing_package_json(self, event):
        self.err('ERROR: no `{}` found in all directories up to the home '
                 'directory.'
                   .format(Package.JSON_PATH))

    def log_missing_dep(self, event, dependency):
        self.err('ERROR: dependency directory `{}` was not accessible when '
                 'attempting to read any contained `{}`.'
                   .format(dependency.full_path, Package.JSON_PATH))

    def log_execute(self, event, package, command):
        self.out('{:<12} executing command `{}`'
                   .format(package + ':', command))

    def log_no_command_handler(self, event, package, command):
        self.out('{:<12} no handler for command `{}`'
                   .format(package + ':', command))

    def log_call(self, event, command, cwd):
        self.out('[{}] {}'
                   .format(cwd, ' '.join(command)))

    def log_update(self, event, package):
        self.out('Updating package {}...'
                   .format(package))

    def log_no_matching_tags(self, event, package, pattern):
        self.err('WARNING: no matching tags in package {} for pattern `{}`.'
                   .format(package, pattern))


