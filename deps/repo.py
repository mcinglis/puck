

from . import git


class Repo:

    type_dispatch = {'git': Git}

    @classmethod
    def from_json_value(cls, jv):
        if isinstance(jv, dict):
            return cls.new(jv['type'], jv['url'])
        else:
            return Git(url=jv)

    @classmethod
    def new(cls, type, url):
        if type not in cls.type_dispatch.keys():
            raise ValueError('unknown repository type')
        return cls.type_dispatch[type](url)

    class Git:
        def __init__(self, url):
            self.url = url

        @property
        def type(self):
            return 'git'

        def update(self, path, tag_pattern=None, checkout=None):
            if os.path.isdir(path):
                git.checkout(path, 'master')
                git.pull(path)
            else:
                git.clone(self.url, path)
            if version.tag_pattern:
                tags = git.tag_list(path, version.tag_pattern)
                if tags:
                    git.checkout(path, max(tags))
                else:
                    return 'no-matching-tags'
            elif version.ref:
                git.checkout(path, ref)



