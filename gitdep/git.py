

from subprocess import check_output, check_call, CalledProcessError, DEVNULL


class NotGitRepository(Exception):
    pass


def root_path(cwd):
    return check_output(
        ['git', 'rev-parse', '--show-toplevel']
    ).decode().strip()


def update(path):
    check_call(['git', 'checkout', 'master'], cwd=path,
               stdout=DEVNULL, stderr=DEVNULL)
    check_call(['git', 'pull'], cwd=path,
               stdout=DEVNULL, stderr=DEVNULL)


def clone(repo_url, path):
    check_call(['git', 'clone', repo_url, path],
               stdout=DEVNULL, stderr=DEVNULL)


def tag_list(path, tag_pattern):
    return check_output(
        ['git', 'tag', '--list', tag_pattern], cwd=path
    ).decode().splitlines()


def checkout(path, commitish):
    subprocess.check_call(['git', 'checkout', commitish], cwd=path,
                          stdout=DEVNULL, stderr=DEVNULL)


