

import json
import re


def object_repr(obj):
    return '{}({})'.format(obj.__class__.__name__,
                           ', '.join('{}={}'.format(k, v)
                                     for k, v in vars(obj).items()))


def load_json(path):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


DERIVE_PATH_PATTERN = re.compile(r'(.*[/:])|(\.git$)|(/$)')

def derive_path(url):
    return DERIVE_PATH_PATTERN.sub('', url)


