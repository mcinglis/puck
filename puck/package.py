
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
from pathlib import Path
from shlex import split as shell_split
from collections import ChainMap

from .repo import Repo
from .errors import (NoPackageJsonError, MissingDependencyError,
                     DependencyConflictError, DuplicatePathError)
from .util import load_json, derive_path, default_caller, call_method


class Package:

    '''
    Represents the data entity formed by the `Package.json` file in the top
    directory of some package.
    '''

    JSON_PATH = Path('Package.json')
    DEPS_DIR  = Path('deps')

    @classmethod
    def from_path(cls, path, **kwargs):
        try:
            return cls.from_json(path=path,
                                 json_path=path / cls.JSON_PATH,
                                 **kwargs)
        except FileNotFoundError as e:
            if path.parent == path:
                raise NoPackageJsonError()
            else:
                return cls.from_path(path.parent, **kwargs)

    @classmethod
    def from_json(cls, path, json_path, require_json=True, **kwargs):
        jsond = (load_json(json_path)
                 if require_json or json_path.exists() else
                 dict())
        return cls(path,
                   dependencies = jsond.get('dependencies'),
                   commands     = jsond.get('commands'),
                   **kwargs)

    def __init__(self, path, deps_dir=None, dependencies=None, commands=None,
                       observers=None, caller=None):
        self.path = path
        assert self.path.is_dir()
        self.caller = caller or default_caller
        self.commands = commands or dict()
        self.observers = observers or list()
        self.deps_dir = deps_dir or self.path / self.__class__.DEPS_DIR
        self.dependencies = [Dependency(self.deps_dir,
                                        observers=self.observers,
                                        caller=self.caller, **d)
                             for d in (dependencies or set())]

    def __str__(self):
        return '{}(path={})'.format(self.__class__.__name__, str(self.path))

    def event(self, event, *args, **kwargs):
        for o in self.observers:
            o.notify(event, *args, **kwargs)

    call = call_method

    def apply_deps(self, f, dev=False):
        for dep in self.dependencies:
            if not dev and dep.dev: continue
            f(dep)

    def update(self, updated=None, verify=True, dev=False):
        updated = updated or []
        self.apply_deps(lambda d: d.update(updated, verify=verify),
                        dev=dev)

    def execute(self, command, executed=None, check=False, env=None,
                      root=True, dev=False):
        executed = executed or []
        self.apply_deps(lambda d: d.execute(command, executed,
                                            check=check, env=env),
                        dev=dev)
        if root:
            self.execute_self(command, check=check, env=env)

    def execute_self(self, command, check=False, env=None):
        if command in self.commands.keys():
            self.event('execute', package=self, command=command)
            c = self.commands[command]
            self.call(c, shell=True, cwd=self.path, check=check, env=env)
        else:
            self.event('no-command-handler', package=self, command=command)


class Dependency:

    '''
    Represents the data entity formed by objects in the `"dependencies"` array
    of a `Package.json` file. Objects of this class are used to clone or update
    the repository to the configured path, and instantiate a new `Package`
    instance to manage that directory (and thus its own dependencies).
    '''

    def __init__(self, deps_dir, repo, path=None, ref=None, tag=None,
                       dev=False, env=None, commands=None, observers=None,
                       caller=None):
        self.deps_dir  = deps_dir
        self.caller    = caller or default_caller
        self.repo      = Repo.from_json_value(repo, observers=observers,
                                              caller=self.caller)
        self.path      = Path(path or derive_path(self.repo.urls[0]))
        self.ref       = ref    # e.g. a commit, branch, or tag
        self.tag       = tag    # tag pattern like 'v3.*'
        self.dev       = dev
        self.env       = env or dict()
        self.commands  = commands or dict()
        self.observers = observers or list()
        self.package   = None

    @property
    def full_path(self):
        return self.deps_dir / self.path

    def __str__(self):
        return '{}(path={})'.format(self.__class__.__name__, str(self.path))

    def event(self, event, *args, **kwargs):
        for o in self.observers:
            o.notify(event, *args, **kwargs)

    call = call_method

    def same(self, other):
        return (set(self.repo.urls) & set(other.repo.urls)
            and self.tag      == other.tag
            and (self.tag or (self.ref == other.ref))
            and self.env      == other.env
            and self.commands == other.commands)

    def path_done(self, deps):
        for d in deps:
            if d.path == self.path:
                if not self.same(d):
                    self.event('dependency-conflict', dep1=d, dep2=self)
                    raise DependencyConflictError()
                return True
        return False

    def load_package(self, force=False):
        if (not self.package) or force:
            if not self.full_path.exists():
                self.event('missing-dependency', dependency=self)
                raise MissingDependencyError()
            self.package = Package.from_path(self.full_path,
                                             deps_dir     = self.deps_dir,
                                             require_json = False,
                                             observers    = self.observers)
            self.package.commands.update(self.commands)

    def update_repo(self, verify=True):
        self.repo.get_latest(self.full_path)
        if self.tag:
            self.repo.checkout_tag(self.full_path, self.tag, verify=verify)
        else:
            self.repo.checkout(self.full_path, self.ref or 'master')

    def update(self, updated, verify=True):
        if self.path_done(updated):
            return
        self.event('update', dependency=self)
        self.update_repo(verify=verify)
        self.load_package(force=True)
        updated.append(self)
        self.package.update(updated=updated, verify=verify)

    def execute(self, command, executed, check=False, env=None):
        if self.path_done(executed):
            return
        self.load_package()
        executed.append(self)
        self.package.execute(command,
                       executed=executed,
                       check=check,
                       env=ChainMap({'DEPS_DIR': str(self.deps_dir.resolve())},
                                    self.env,
                                    env or dict()))


