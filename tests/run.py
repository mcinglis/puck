#!/bin/env python3

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
from subprocess import check_call, DEVNULL


def read_file(path):
    with open(path) as f:
        return f.read()


def exists(path):
    return os.access(path, os.F_OK)


def call(args, **kwargs):
    print(*args)
    check_call(args, **kwargs)


TEST_SEP = '###############################################'
def test(f):
    def wrap():
        print('{sep}\n    START TEST: {name}\n{sep}'
                .format(sep=TEST_SEP, name=f.__name__))
        f()
        print('{sep}\n    END TEST:   {name}\n{sep}\n'
                .format(sep=TEST_SEP, name=f.__name__))
    return wrap


@test
def test_package1():
    cwd = 'package1'

    call(['puck', 'update'], cwd=cwd)
    assert not exists('package1/deps')

    call(['puck', 'execute', 'build', '--root'], cwd=cwd)
    assert read_file('package1/output') == 'default package1 var\n'


@test
def test_package3():
    cwd = 'package3'

    call(['puck', 'update', '--no-verify'], cwd=cwd)
    assert all([
        exists('package3/deps/package1'),
        exists('package3/deps/package2')
    ])

    call(['puck', 'execute', 'build'], cwd=cwd)
    assert all([
        read_file('package3/deps/package1/output') == 'default package1 var\n',
        read_file('package3/deps/package2/output') == 'second commit: set!\n'
    ])


@test
def test_package4():
    cwd = 'package4'

    call(['puck', 'update', '--no-verify'], cwd=cwd)
    assert all([
        exists('package4/deps/package1'),
        exists('package4/deps/package2'),
        exists('package4/deps/package3')
    ])

    call(['puck', 'execute', 'build'], cwd=cwd)
    assert all([
        read_file('package4/deps/package1/output') == 'default package1 var\n',
        read_file('package4/deps/package2/output') == 'second commit: set!\n',
        read_file('package4/deps/package3/output') == 'building package 3\n',
    ])


@test
def test_package5():
    cwd = 'package5'

    call(['puck', 'update', '--no-verify'], cwd=cwd)
    assert all([
        exists('package5/deps/package1'),
        exists('package5/deps/package2'),
        exists('package5/deps/package3'),
        exists('package5/deps/package4')
    ])

    call(['puck', 'execute', 'build'], cwd=cwd)
    assert all([
        read_file('package5/deps/package1/output') == 'default package1 var\n',
        read_file('package5/deps/package2/output') == 'second commit: set!\n',
        read_file('package5/deps/package3/output') == 'building package 3\n',
        read_file('package5/deps/package4/output') == 'building package 4\n',
    ])


def main():
    if not all(exists(d) for d in
               ('package' + str(n) for n in range(1, 6))):
        print('Please run `./setup.bash` first.')
        return 1

    test_package1()
    test_package3()
    test_package4()
    test_package5()
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())

