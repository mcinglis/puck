

from subprocess import check_output, check_call, CalledProcessError, DEVNULL


def checkout(path, commitish):
    check_call(['git', 'checkout', commitish], cwd=path)


def clone(repo, path):
    check_call(['git', 'clone', repo, path])


def pull(path):
    check_call(['git', 'pull'], cwd=path)


def tag_list(path, tag_pattern):
    return check_output(
        ['git', 'tag', '--list', tag_pattern], cwd=path
    ).decode().splitlines()


