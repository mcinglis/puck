
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
from shlex import split as shell_split
from collections import ChainMap

from .repo import Repo
from .errors import (NoPackageJsonError, MissingDependencyError,
                     DependencyCycleError)
from .util import (load_json, derive_path, event_method, default_caller,
                   call_method)


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
            return cls.from_json(path=path,
                                 json_path=os.path.join(path, cls.JSON_PATH),
                                 **kwargs)
        except FileNotFoundError as e:
            if not path or os.path.samefile(path, os.path.expanduser('~')):
                raise NoPackageJsonError()
            else:
                return cls.from_path(os.path.dirname(path), **kwargs)

    @classmethod
    def from_json(cls, path, json_path, require_json=True, **kwargs):
        jsond = (load_json(json_path)
                 if require_json or os.access(json_path, os.F_OK) else
                 dict())
        return cls(path,
                   dependencies = jsond.get('dependencies'),
                   commands     = jsond.get('commands'),
                   **kwargs)

    def __init__(self, path, dependencies=None, commands=None,
                       observers=None, caller=None):
        self.path = path
        self.caller = caller or default_caller
        self.commands = commands or dict()
        self.observers = observers or list()
        self.dependencies = [Dependency(self.deps_dir,
                                        observers=self.observers,
                                        caller=self.caller, **d)
                             for d in (dependencies or set())]

    @property
    def deps_dir(self):
        return os.path.join(self.path, self.__class__.DEPS_DIR)

    def __str__(self):
        return '{}(path={})'.format(self.__class__.__name__, self.path)

    event = event_method

    call = call_method

    def apply_deps(self, f, dev=False):
        for dep in self.dependencies:
            if not dev and dep.dev: continue
            f(dep)

    def update(self, updated=None, verify=True, dev=False):
        self.apply_deps(lambda d: d.update(updated or [], verify=verify),
                        dev=dev)

    def execute(self, command, executed=None, check=False, env=None,
                      root=True, dev=False):
        self.apply_deps(lambda d: d.execute(command, executed or [],
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
            self.event('no-command-handler', command=command)

    def wipe(self, force=False, dev=False):
        self.apply_deps(lambda d: d.wipe(force=force),
                        dev=dev)


class Dependency:

    '''
    Represents the data entity formed by objects in the `"dependencies"` array
    of a `Package.json` file. Objects of this class are used to clone or update
    the repository to the configured path, and instantiate a new `Package`
    instance to manage that directory (and thus its own dependencies).
    '''

    def __init__(self, in_dir, repo, path=None, ref=None, tag=None, dev=False,
                       env=None, commands=None, observers=None, caller=None):
        self.in_dir    = in_dir
        self.caller    = caller or default_caller
        self.repo      = Repo.from_json_value(repo, observers=observers,
                                              caller=self.caller)
        self.path      = path or derive_path(self.repo.url)
        self.ref       = ref    # e.g. a commit, branch, or tag
        self.tag       = tag    # tag pattern like 'v3.*'
        self.dev       = dev
        self.env       = env or dict()
        self.commands  = commands or dict()
        self.observers = observers or list()
        self.package   = None

    @property
    def full_path(self):
        return os.path.join(self.in_dir, self.path)

    def __str__(self):
        return '{}(full_path={})'.format(self.__class__.__name__,
                                         self.full_path)

    event = event_method

    call = call_method

    def same(self, other):
        return (self.repo     == other.repo
            and self.tag      == other.tag
            and (self.tag or self.ref == other.ref)
            and self.env      == other.env
            and self.commands == other.commands)

    def same_in(self, others):
        return any(d for d in others if self.same(d))

    def load_package(self, force=False):
        if (not self.package) or force:
            if not os.access(self.full_path, os.F_OK):
                self.event('missing-dependency', dependency=self)
                raise MissingDependencyError()
            self.package = Package.from_path(self.full_path,
                                             require_json = False,
                                             observers    = self.observers)
            self.package.commands.update(self.commands)

    def update_repo(self, verify=True):
        self.repo.get_latest(self.full_path)
        if self.tag:
            self.repo.checkout_tag(self.full_path, self.tag, verify=verify)
        else:
            self.repo.checkout(self.full_path, self.ref or 'master')

    def dependency_cycle_err(self):
        self.event('dependency-cycle', dependency=self)
        raise DependencyCycleError()

    def update(self, updated, verify=True):
        if self.same_in(updated):
            self.dependency_cycle_err()
        self.event('update', dependency=self)
        self.update_repo(verify=verify)
        self.load_package(force=True)
        updated.append(self)
        self.package.update(updated=updated, verify=verify)

    def execute(self, command, executed, check=False, env=None):
        if self.same_in(executed):
            self.dependency_cycle_err()
        self.load_package()
        executed.append(self)
        self.package.execute(command, executed=executed,
                                      check=check,
                                      env=ChainMap(self.env, env or dict()))

    def wipe(self, force=False):
        if os.access(self.full_path, os.F_OK):
            self.call(['rm', '-rf' + ('' if force else 'I'), self.full_path])


