
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
from subprocess import check_call, check_output

from .util import derive_path, event


class GitRepo:

    def __init__(self, url, observers=None):
        self.url = os.path.expanduser(url)
        self.observers = observers or list()

    def __eq__(self, other):
        return (self.type == other.type
            and self.url == other.url)

    @property
    def type(self):
        return 'git'

    event = event

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

    def tag_list(self, path, pattern):
        return self.call(['git', 'tag', '--list', pattern], cwd=path,
                         output=True)

    def tag_verify(self, path, tag):
        self.call(['git', 'tag', '--verify', tag], cwd=path)

    def checkout_tag(self, path, pattern, verify=True):
        tags = self.tag_list(path, pattern)
        if tags:
            tag = max(tags)
            if verify:
                self.tag_verify(path, tag)
            self.checkout(path, tag)
        else:
            self.event('no-matching-tags', path=path, pattern=pattern)

    def checkout(self, path, s):
        self.call(['git', 'checkout', s], cwd=path)


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


