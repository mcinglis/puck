

from subprocess import check_output, check_call, CalledProcessError, DEVNULL


class NotGitRepository(Exception):
    pass


def root_path(cwd):
    return check_output(
        ['git', 'rev-parse', '--show-toplevel']
    ).decode().strip()


def pull_master(path):
    check_call(['git', 'checkout', 'master'], cwd=path)
    check_call(['git', 'pull'], cwd=path)


def clone(repo, path):
    check_call(['git', 'clone', repo, path])


def tag_list(path, tag_pattern):
    return check_output(
        ['git', 'tag', '--list', tag_pattern], cwd=path
    ).decode().splitlines()


def checkout(path, commitish):
    check_call(['git', 'checkout', commitish], cwd=path)


