
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


import os
import re
from subprocess import call, check_call
from shlex import split as shell_split

from .repo import Repo
from .util import load_json, derive_path, event


class Package:

    '''
    Represents the data entity formed by the `Package.json` file in the top
    directory of some package.
    '''

    JSON_PATH = 'Package.json'
    DEPS_DIR  = 'deps'

    @classmethod
    def from_path(cls, path, **kwargs):
        try:
            return cls.from_json(root_path=path,
                                 json_path=os.path.join(path, cls.JSON_PATH),
                                 **kwargs)
        except FileNotFoundError as e:
            if os.path.samefile(path, os.path.expanduser('~')):
                raise e
            else:
                return cls.from_path(os.path.dirname(path), **kwargs)

    @classmethod
    def from_json(cls, root_path, json_path, require_json=True, **kwargs):
        jsond = (load_json(json_path)
                 if require_json or os.access(json_path, os.F_OK) else
                 dict())
        return cls.from_dict(root_path, jsond, **kwargs)

    @classmethod
    def from_dict(cls, root_path, d, **kwargs):
        return cls(root_path,
                   deps     = d.get('dependencies', None),
                   commands = d.get('commands', None),
                   **kwargs)

    def __init__(self, root_path, deps_dir=None, deps=None, commands=None,
                       name=None, observers=None):
        self.root_path = root_path
        self.deps_dir  = deps_dir or os.path.join(self.root_path,
                                                  self.__class__.DEPS_DIR)
        self.deps = {Dependency(self.deps_dir, observers=observers, **d)
                     for d in (deps or set())}
        self.commands = commands or dict()
        self.observers = observers or list()
        self.name = name or os.path.basename(os.path.realpath(self.root_path))

    def __str__(self):
        return '{}(root_path={})'.format(self.__class__.__name__,
                                         self.root_path)

    event = event

    def select_deps(self, dev):
        return self.deps if dev else {d for d in self.deps if not d.dev}

    def call(self, command, check=False, env=None):
        self.event('call', command=command, cwd=self.root_path)
        if check:
            check_call(command, cwd=self.root_path, env=None)
        else:
            call(command, cwd=self.root_path, env=None)

    def update(self, updated=None, verify=True, dev=False):
        updated = updated or set()
        for dep in self.select_deps(dev):
            updated |= dep.update(updated, verify=verify)
        return updated

    def execute(self, command, executed=None, env=None, check=False,
                      me_too=True, dev=False):
        executed = executed or set()
        # Execute the given command in all dependencies:
        for dep in self.select_deps(dev):
            executed |= dep.execute(command, executed, env=env, check=check)
        # Execute the given command for this package, unless told otherwise:
        if me_too:
            if command in self.commands.keys():
                self.event('execute', command=command)
                self.call(self.commands[command], check=check, env=env)
            else:
                self.event('no-command-handler', command=command)
        return executed

    def wipe(self, force=True, dev=False):
        for dep in self.select_deps(dev):
            if os.access(dep.full_path, os.F_OK):
                self.call(['rm', '-rf' + ('' if force else 'I'),
                           dep.full_path])


class Dependency:

    '''
    Represents the data entity formed by objects in the `"dependencies"` array
    of a `Package.json` file. Objects of this class are used to clone or update
    the repository to the configured path, and instantiate a new `Package`
    instance to manage that directory (and thus its own dependencies).
    '''

    _version_tag_pattern = re.compile(r'^v(?P<major>\d)\.((\*)|'
                                       r'((?P<minor>\d)\.((\*)|'
                                       r'(?P<patch>\d))))$')

    @classmethod
    def _path_suffix_from_version(cls, tag):
        if not tag:
            return ''
        m = cls._version_tag_pattern.match(tag)
        if m:
            return '-' + '.'.join(n
                                  for n in m.group('major', 'minor', 'patch')
                                  if n)
        else:
            return ''

    @classmethod
    def from_dict(cls, d, **kwargs):
        kwargs.update(d)
        return cls(**kwargs)

    def __init__(self, deps_dir, repo, path=None, ref=None, tag=None,
                       dev=False, env=None, commands=None, observers=None):
        self.deps_dir  = deps_dir
        self.repo      = Repo.from_json_value(repo, observers=observers)
        self.ref       = ref    # commit, branch, or tag
        self.tag       = tag    # tag pattern like 'v3.*'
        self.dev       = dev
        self.env       = env or dict()
        self.commands  = commands or dict()
        self.path      = (path or
                          (derive_path(self.repo.url)
                         + self.__class__._path_suffix_from_version(self.tag)))
        self.observers = observers or list()
        self.package   = None

    @property
    def full_path(self):
        return os.path.join(self.deps_dir, self.path)

    def __str__(self):
        return '{}(full_path={})'.format(self.__class__.__name__,
                                         self.full_path)

    event = event

    def load_package(self, force=False):
        if (not self.package) or force:
            if not os.access(self.full_path, os.F_OK):
                self.event('missing-dep', dependency=self)
                self.package = None
                return False
            self.package = Package.from_path(
                               self.full_path,
                               require_json = False,
                               deps_dir     = os.path.abspath(self.deps_dir),
                               observers    = self.observers,
                               name         = self.path)
        return True

    def same(self, other):
        return (self.repo     == other.repo
            and self.tag      == other.tag
            and (self.tag or self.ref == other.ref)
            and self.env      == other.env
            and self.commands == other.commands)

    def conflicts_with(self, deps):
        for d in deps:
            if d.path == self.path:
                if not self.same(d):
                    self.event('conflict', d)
                return True
        return False

    def update_repo(self, verify=True):
        self.repo.get_latest(self.full_path)
        if self.tag:
            self.repo.checkout_tag(self.full_path, self.tag, verify=verify)
        else:
            self.repo.checkout(self.full_path, self.ref or 'master')

    def update(self, updated, verify=True):
        if self.conflicts_with(updated):
            return updated
        self.event('update', package=self.package)
        self.update_repo(verify=verify)
        updated |= {self}
        if self.load_package(force=True):
            return self.package.update(updated=updated)
        else:
            return updated

    def execute(self, command, executed, env=None, check=False):
        if self.conflicts_with(executed):
            return executed
        executed |= {self}
        if self.load_package():
            env = dict(list((env or dict()).items())
                     + list(self.env.items()))
            if command in self.commands.keys():
                self.package.event('execute', command=command)
                self.package.call(self.commands[command], env=env, check=check)
            else:
                executed |= self.package.execute(command,
                                                 executed=executed,
                                                 env=env,
                                                 check=check)
        return executed


