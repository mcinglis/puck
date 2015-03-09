
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
from subprocess import check_call, check_output, CalledProcessError

from .util import default_caller, call_method
from .errors import RepoVerificationError


class Repo:

    @classmethod
    def from_json_value(cls, jv, **kwargs):
        if isinstance(jv, list):
            return cls(urls=jv, **kwargs)
        else:
            return cls(urls=[jv], **kwargs)

    def __init__(self, urls, observers=None, caller=None):
        self.urls = [os.path.expanduser(url) for url in urls]
        self.observers = observers or list()
        self.caller = caller or default_caller

    @property
    def url(self):
        return self.urls[0]

    def event(self, event, *args, **kwargs):
        for o in self.observers:
            o.notify(event, *args, **kwargs)

    call = call_method

    def get_latest(self, path):
        if path.is_dir():
            self.call(['git', 'fetch', '--tags'], cwd=path)
        else:
            self.call(['git', 'clone', self.url, str(path)], cwd='.')

    def tag_list(self, path, pattern):
        return self.call(['git', 'tag', '--list', pattern], cwd=path,
                         output=True).splitlines()

    def tag_verify(self, path, tag):
        try:
            self.call(['git', 'tag', '--verify', tag], cwd=path)
        except CalledProcessError:
            raise RepoVerificationError()

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


