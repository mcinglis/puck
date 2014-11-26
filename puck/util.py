

import json
import re


def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)


DERIVE_PATH_REGEX = re.compile(r'(.*[/:])|(\.git$)|(/$)')

def derive_path(url):
    return DERIVE_PATH_REGEX.sub('', url)


