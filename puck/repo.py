

import os
from subprocess import check_call, check_output

from .util import derive_path


class GitRepo:

    def __init__(self, url, observer=None):
        self.url = os.path.expanduser(url)
        self.observer = observer

    def __eq__(self, other):
        return (self.type == other.type
            and self.url == other.url)

    @property
    def type(self):
        return 'git'

    def event(self, event, **kwargs):
        if self.observer:
            self.observer.notify(event, source=self, **kwargs)

    def call(self, command, cwd=None, output=False):
        self.event('call', command=command, cwd=cwd)
        if output:
            return check_output(command, cwd=cwd).decode().splitlines()
        else:
            check_call(command, cwd=cwd)

    def get_latest(self, path):
        if os.path.isdir(path):
            self.call(['git', 'fetch', '--tags'], cwd=path)
        else:
            self.call(['git', 'clone', self.url, path], cwd='.')

    def list_tags(self, path, pattern):
        return self.call(['git', 'tag', '--list', pattern], cwd=path,
                         output=True)

    def verify(self, path, tag):
        self.call(['git', 'tag', '--verify', tag], cwd=path)

    def checkout_tag(self, path, pattern, verify=True):
        tags = self.list_tags(path, pattern)
        if tags:
            tag = max(tags)
            if verify:
                self.verify(path, tag)
            self.checkout(path, tag)
        else:
            self.event('no-matching-tags', path=path, pattern=pattern)

    def checkout(self, path, s):
        self.call(['git', 'checkout', s], cwd=path)

    def update(self, path, tag_pattern=None, ref=None, verify=True):
        self.get_latest(path)
        if tag_pattern:
            self.checkout_tag(path, tag_pattern, verify=verify)
        else:
            self.checkout(path, ref or 'master')


class MercurialRepo:
    def __init__(self, *args, **kwargs):
        raise NotImplementedError()


class Repo:

    type_dispatch = {'git': GitRepo,
                     'hg': MercurialRepo}

    @classmethod
    def from_json_value(cls, jv, **kwargs):
        if isinstance(jv, str):
            return GitRepo(url=jv, **kwargs)
        else:
            if len(jv) != 1:
                raise ValueError('repo JSON object should only have a single '
                                 'key-value pair, representing the type and '
                                 'URL respectively')
            typ, url = list(jv.items())[0]
            return cls.new(typ, url, **kwargs)

    @classmethod
    def new(cls, typ, url, **kwargs):
        if typ not in cls.type_dispatch.keys():
            raise ValueError('unknown repository type "{}" for <{}>'
                             .format(typ, url))
        return cls.type_dispatch[typ](url, **kwargs)


