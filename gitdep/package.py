

import os

from . import git
from .util import object_repr, load_json, derive_path


class Package:

    DEFAULT_JSON_PATH = 'Package.json'
    DEFAULT_DEPS_DIR = 'dependencies'

    @classmethod
    def from_path(cls, root_path, dev_deps=False, logger=None):
        return cls.from_json(root_path,
                             os.path.join(root_path, cls.DEFAULT_JSON_PATH),
                             dev_deps=dev_deps, logger=logger)

    @classmethod
    def from_json(cls, root_path, json_path, dev_deps=False, logger=None):
        jsond = load_json(json_path)
        return cls(root_path,
                   deps={Dependency.from_dict(d, logger=logger)
                         for d in (jsond.get('dependencies', [])
                                   + (jsond.get('dev_dependencies', [])
                                      if dev_deps else []))},
                   deps_dir=jsond.get('dependencies_dir', None))

    def __init__(self, root_path, deps=None, deps_dir=None):
        self.root_path = root_path
        self.deps      = deps or set()
        self.deps_dir  = (deps_dir or self.__class__.DEFAULT_DEPS_DIR)

    def __repr__(self):
        return object_repr(self)

    def __str__(self):
        return repr(self)

    def path_maker(self, dep_path):
        return os.path.join(self.root_path, self.deps_dir, dep_path)

    def update(self, updated=None, path_maker=None):
        updated = updated or set()
        path_maker = path_maker or self.path_maker
        for dep in self.dependencies:
            updated |= dep.update(updated, path_maker)
        return updated


class Dependency:

    @classmethod
    def from_dict(cls, d, logger=None):
        if 'repo' in d.keys():
            return cls(d['repo'], logger=logger, **d)
        else:
            if len(d) > 1:
                raise ValueError('short form of dependency object should ' +
                                 'only have a single key-value pair, with ' +
                                 'the repo URL as key, and tag pattern as ' +
                                 'value')
            repo, tag_pattern = list(d.items())[0]
            return cls(repo, tag_pattern=tag_pattern, logger=logger)

    def __init__(self, repo, path=None, tag_pattern=None, checkout=None,
                       logger=None):
        if not repo:
            raise ValueError('repo field is required')
        self.repo        = repo
        self.path        = path or derive_path(self.repo)
        self.tag_pattern = tag_pattern or ''
        self.checkout    = checkout or ''
        self.logger      = logger
        # Set by `self.update()`:
        self.package     = None
        self.full_path   = None

    def __repr__(self):
        r = '{}(repo={}, path={}'.format(self.__class__, self.repo, self.path)
        if self.tag_pattern:
            r += ', tag_pattern={}'.format(self.tag_pattern)
        if self.checkout:
            r += ', checkout={}'.format(self.checkout)
        if self.logger:
            r += ', logger={}'.format(repr(self.logger))
        return r + ')'

    def __str__(self):
        return repr(self)

    def log(self, event, *args, **kwargs):
        if self.logger:
            self.logger(*args, event=event, source=self, **kwargs)

    def update(self, updated, path_maker):
        updated = updated or set()
        self.full_path = path_maker(self.path)
        for dep in updated:
            if dep.full_path == None:
                raise ValueError('dependency with unset full path')
            if dep.full_path == self.full_path:
                if dep != self:
                    self.log('conflict', dep)
                return updated
        self.log('updating-dep')
        self.update_repo()
        self.package = Package.from_path(self.full_path, logger=logger)
        return self.package.update(updated=(updated | {self}),
                                   path_maker=path_maker)

    def update_repo(self):
        if os.path.isdir(self.full_path):
            git.update(self.full_path)
        else:
            git.clone(self.url, self.full_path)
        if self.tag_pattern:
            tags = git.tag_list(self.full_path, self.tag_pattern)
            if not tags:
                self.log('no-matching-tags', self.tag_pattern)
            git.checkout(self.full_path, max(tags))
        elif self.checkout:
            git.checkout(self.full_path, self.checkout)


