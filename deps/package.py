

import os
from subprocess import check_call, DEVNULL

from . import git
from .util import object_repr, load_json, derive_path


def log(self, event, *args, **kwargs):
    if self.logger:
        self.logger.notify(event, self, *args, **kwargs)


class Package:

    DEFAULT_JSON_PATH = 'Package.json'
    DEFAULT_DEPS_DIR = 'dependencies'

    @classmethod
    def from_path(cls, path, deps_dir=None, dev_deps=False, logger=None):
        return cls.from_root_path(git.root_path(path), deps_dir=deps_dir,
                                  dev_deps=dev_deps, logger=logger)

    @classmethod
    def from_root_path(cls, root_path, deps_dir=None,
                            dev_deps=False, logger=None):
        return cls.from_json(root_path,
                             os.path.join(root_path, cls.DEFAULT_JSON_PATH),
                             deps_dir=deps_dir, dev_deps=False, logger=logger)

    @classmethod
    def from_json(cls, root_path, json_path, deps_dir=None,
                       dev_deps=False, logger=None):
        jsond = load_json(json_path) if os.path.isfile(json_path) else dict()
        return cls(root_path,
                   jsond.get('dependencies', [])
                   + (jsond.get('dev_dependencies', [])
                      if dev_deps else []),
                   deps_dir=deps_dir or jsond.get('dependencies_dir', None),
                   build_cmd=jsond.get('build', None),
                   logger=logger)

    def __init__(self, root_path, deps=None, deps_dir=None, build_cmd=None,
                       logger=None):
        self.root_path = root_path
        self.deps_dir = (deps_dir
                      or os.path.join(self.root_path,
                                      self.__class__.DEFAULT_DEPS_DIR))
        self.deps = {Dependency.from_dict(d, self.deps_dir, logger=logger)
                     for d in deps}
        self.build_cmd = build_cmd or []
        self.logger = logger

    def __repr__(self):
        return object_repr(self)

    def __str__(self):
        return repr(self)

    log = log

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
    def from_dict(cls, d, deps_dir, logger=None):
        if 'repo' in d.keys():
            return cls(deps_dir=deps_dir, logger=logger, **d)
        else:
            if len(d) > 1:
                raise ValueError('short form of dependency object should ' +
                                 'only have a single key-value pair, with ' +
                                 'the repo URL as key, and tag pattern as ' +
                                 'value')
            repo, tag_pattern = list(d.items())[0]
            return cls(repo, deps_dir, tag_pattern=tag_pattern, logger=logger)

    def __init__(self, repo, deps_dir, path=None, tag_pattern=None,
                       checkout=None, env=None, logger=None):
        self.repo        = repo
        self.deps_dir    = deps_dir
        self.path        = os.path.join(deps_dir,
                                        path or derive_path(self.repo))
        self.tag_pattern = tag_pattern or ''
        self.checkout    = checkout or ''
        self.env         = dict(list(os.environ.items())
                              + list((env or dict()).items())
                              + [('DEPS_DIR', self.deps_dir)])
        self.logger      = logger
        self.package     = None     # set by `self.load()`

    def __repr__(self):
        r = ('{}(repo={}, deps_dir={}, path={}'
             .format(self.__class__.__name__,
                     self.repo, self.deps_dir, self.path))
        if self.tag_pattern:
            r += ', tag_pattern={}'.format(self.tag_pattern)
        elif self.checkout:
            r += ', checkout={}'.format(self.checkout)
        return r + ')'

    def __str__(self):
        return repr(self)

    def same(self, other):
        return (self.repo == other.repo
            and self.env == other.env
            and self.tag_pattern == other.tag_pattern
            and (self.tag_pattern
              or self.checkout == other.checkout))

    log = log

    def conflicts(self, deps, log_event):
        for d in deps:
            if d.path == self.path:
                if not self.same(d):
                    self.log(log_event, d)
                return True
        return False

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
        self.update_repo()
        self.load_package()
        return self.package.update_deps(updated=updated | {self})

    def build(self, built=None):
        built = built or set()
        if self.conflicts(built, 'dep-build--conflict'):
            return built
        self.load_package()
        return self.package.build(self.env, built=built | {self})

