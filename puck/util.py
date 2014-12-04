
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


import json
import re
import subprocess


def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)


DERIVE_PATH_REGEX = re.compile(r'(.*[/:])|(\.git$)|(/$)')

def derive_path(url):
    return DERIVE_PATH_REGEX.sub('', url)


def event_method(self, event, *args, **kwargs):
    for o in self.observers:
        o.notify(event, *args, **kwargs)


def default_caller(args, output=False, check=True, **kwargs):
    if output:
        return subprocess.check_output(args, universal_newlines=True, **kwargs)
    elif check:
        subprocess.check_call(args, **kwargs)
    else:
        subprocess.call(args, **kwargs)


def call_method(self, args, **kwargs):
    self.event('call', args=args, cwd=kwargs.get('cwd'))
    return self.caller(args, **kwargs)


