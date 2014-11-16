

import os

from . import git
from .util import object_repr, load_json, derive_path


def dir_has_package_json(path):
    return os.access(os.path.join(path, Package.JSON_PATH), os.F_OK)


def log(self, event, *args, **kwargs):
    if self.logger:
        self.logger.notify(event, self, *args, **kwargs)


class Package:

    JSON_PATH        = 'Package.json'
    DEPENDENCIES_DIR = 'dependencies'

    @classmethod
    def from_path(cls, path, require_json=True, **kwargs):
        try:
            return cls.from_json(root_path=path,
                                 json_path=os.path.join(path, cls.JSON_PATH),
                                 require_json=require_json,
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
        # TODO: proper validation of JSON
        return cls.from_dict(root_path, jsond, **kwargs)

    @classmethod
    def from_dict(cls, root_path, d, **kwargs):
        return cls(root_path        = root_path,
                   dependencies     = d.get('dependencies', None),
                   commands         = d.get('commands', None),
                   **kwargs)

    def __init__(self, root_path, dependencies=None, command_delegate=None,
                       commands=None, dependencies_root=None, logger=None):
        self.root_path = root_path
        self.dependencies_root = (dependencies_root
                              or os.path.join(self.root_path,
                                              self.__class__.DEPENDENCIES_DIR))
        self.dependencies = {Dependency.from_dict(d, self.dependencies_root,
                                                  logger=logger)
                             for d in (dependencies or set())}
        self.commands = commands or dict()
        self.logger = logger

    @property
    def dev_dependencies(self):
        return [d for d in self.dependencies if d.dev]

    def __str__(self):
        return '{}(root_path={})'.format(self.__class__.__name__,
                                         self.root_path)

    log = log

    def all_deps(self, dev=False):
        deps = self.dependencies if dev else {d for d in self.dependencies
                                                if not d.dev}
        for d in deps:
            d_deps = d.package.all_deps()
            if any_conflicts(deps, d_deps):
                self.log('conflict', 

    def update_deps(self, dev=False, updated=None):
        updated = updated or set()
        deps = self.dependencies if dev else [d for d in self.dependencies
                                                if not d.dev]
        for d in deps:
            updated |= d.update(updated=updated)
        return updated

    def execute(self, command, executed=None):
        executed = executed or set()
        for d in self.dependencies:
            d.kkkkkkkkkkkkk
        pass

    def build(self, env, built=None):
        built = self.build_deps(built=built or set())
        if self.build_cmd:
            self.log('package-build')
            check_call(self.build_cmd, cwd=self.root_path, env=env,
                       stdout=DEVNULL, stderr=DEVNULL)
        return built

    def update_deps(self, updated=None):
        updated = updated or set()
        for d in self.deps:
            updated |= d.update(updated=updated)
        return updated

    def build_deps(self, built=None):
        built = built or set()
        for d in self.deps:
            built |= d.build(built=built)
        return built



class Dependency:

    @classmethod
    def from_dict(cls, d, root, **kwargs):
        if 'repo' in d.keys():
            return cls(root        = root,
                       repo        = d['repo'],
                       path        = d.get('path', None),
                       tag_pattern = d.get('tag_pattern', None),
                       checkout    = d.get('checkout', None),
                       env         = d.get('env', None),
                       dev         = d.get('dev', False)
                       **kwargs)
        else:
            if len(d) != 1:
                raise ValueError('short form of dependency JSON object '
                                 'should only have a single key-value')
            repo, tag_pattern = list(d.items())[0]
            return cls(root=root, repo=repo, tag_pattern=tag_pattern, **kwargs)

    def __init__(self, root, repo, path=None, tag_pattern=None, checkout=None,
                       env=None, dev=False, logger=None):
        self.root     = root
        self.repo     = Repo.from_json_value(repo)
        self.path     = os.path.join(root, path or derive_path(repo.url))
        self.tag      = tag or ''
        self.checkout = checkout or ''
        self.env      = dict(list(os.environ.items())
                           + list((env or dict()).items())
                           + [('DEPENDENCIES_ROOT', self.root)])
        self.dev      = dev
        self.logger   = logger
        self.package  = None

    def __str__(self):
        return '{}(path={})'.format(self.__class__.__name__, self.path)

    def same(self, other):
        return (self.repo == other.repo
            and self.tag  == other.tag
            and (self.tag or (self.checkout == other.checkout))
            and self.env  == other.env)

    log = log

    def conflicts(self, deps, log_event):
        for d in deps:
            if d.path == self.path:
                if not self.same(d):
                    self.log(log_event, d)
                return True
        return False

    def update(self

    def load_package(self):
        if not self.package:
            self.log('dep-load-package')
            self.package = Package.from_root_path(self.path,
                                                  deps_dir=self.deps_dir,
                                                  logger=self.logger)

    def update_repo(self):
        if os.path.isdir(self.path):
            self.log('dep-update--pull-master')
            git.pull_master(self.path)
        else:
            self.log('dep-update--clone')
            git.clone(self.repo, self.path)
        if self.tag_pattern:
            tags = git.tag_list(self.path, self.tag_pattern)
            if not tags:
                self.log('dep-update--no-matching-tags', self.tag_pattern)
            else:
                tag = max(tags)
                self.log('dep-update--checkout', tag)
                git.checkout(self.path, tag)
                # TODO: git verify signature
        elif self.checkout:
            self.log('dep-update--checkout', self.checkout)
            git.checkout(self.path, self.checkout)

    def update(self, updated=None):
        updated = updated or set()
        if self.conflicts(updated, 'dep-update--conflict'):
            return updated
        self.log('dep-update')
        self.repo.update(self.path,
                         tag_pattern=self.tag_pattern,
                         checkout=self.checkout)
        self.load_package()
        return self.package.update_deps(updated=updated | {self})

    def build(self, built=None):
        built = built or set()
        if self.conflicts(built, 'dep-build--conflict'):
            return built
        self.load_package()
        return self.package.build(self.env, built=built | {self})


