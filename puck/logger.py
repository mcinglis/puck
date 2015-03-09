
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

    def __init__(self, outfile, errfile, on_err=None):
        self.outfile = outfile
        self.errfile = errfile
        self.dispatch = {
            'no-package-json':      self.log_no_package_json,
            'execute':              self.log_execute,
            'no-command-handler':   self.log_no_command_handler,
            'call':                 self.log_call,
            'update':               self.log_update,
            'no-matching-tags':     self.log_no_matching_tags,
            'missing-dependency':   self.log_missing_dependency,
            'dependency-conflict':  self.log_dependency_conflict
        }

    def __str__(self):
        return '{}(outfile={}, errfile={})'.format(self.__class__.__name__,
                                                   self.outfile, self.errfile)

    def out(self, *args, **kwargs):
        if self.outfile:
            print(*args, file=self.outfile, **kwargs)

    def err(self, *args, exitcode=1, **kwargs):
        if self.errfile:
            print(*args, file=self.errfile, **kwargs)

    def notify(self, event, **kwargs):
        self.dispatch.get(event, self.log_default)(event, **kwargs)

    def log_default(self, event, **kwargs):
        self.err('WARNING: event `{}` received: kwargs={}'
                   .format(event, kwargs))

    def log_no_package_json(self, event):
        self.err('ERROR: no `{}` found in all directories up to the home '
                 'directory.'
                   .format(Package.JSON_PATH))

    def log_missing_dependency(self, event, dependency):
        self.err('ERROR: dependency directory `{}` is missing.'
                   .format(dependency.full_path, Package.JSON_PATH))

    def log_dependency_conflict(self, event, dep1, dep2):
        self.err('ERROR: dependency at `{}` has URLs `{}`, none of which are '
                 'in the set of URLs of the dependency already updated at '
                 'that path: `{}`'
                   .format(dep1.full_path, dep2.repo.urls, dep1.repo.urls))

    def log_execute(self, event, package, command):
        self.out('### {}: executing command `{}`...'
                   .format(package.path, command))

    def log_no_command_handler(self, event, package, command):
        self.out('### {}: no handler for command `{}`'
                   .format(package.path, command))

    def log_call(self, event, args, cwd=None):
        if cwd:
            self.out('[{}]'.format(cwd), end=' ')
        self.out(args if isinstance(args, str) else ' '.join(args))

    def log_update(self, event, dependency):
        self.out('\n### Updating dependency at: {}'
                   .format(dependency.full_path))

    def log_no_matching_tags(self, event, package, pattern):
        self.err('WARNING: no matching tags in package {} for pattern `{}`.'
                   .format(package, pattern))



