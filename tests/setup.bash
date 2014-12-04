#!/bin/bash

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


set -o errexit
set -o pipefail
set -o nounset


setup_package1() {
    mkdir package1
    cd package1
    git init
    touch f1 f2
    git add .
    git commit --message "Commit 1"
    git tag --annotate v1.0.0 --message ""
    touch f3
    git add .
    git commit --message "Commit 2"
    git tag --annotate v1.1.0 --message ""
    cat > Package.json <<EOF
{
    "commands": { "build": "make" }
}
EOF
    cat > Makefile <<EOF
PACKAGE1_VAR ?= default package1 var
all:
	echo "\$(PACKAGE1_VAR)" > output
EOF
    git add .
    git commit --message "Commit 3"
    git tag --annotate v1.2.0 --message ""
    cd ..
}


setup_package2() {
    mkdir package2
    cd package2
    git init
    touch f1 f2
    git add .
    git commit --message "Commit 1"
    git tag --annotate v2.0.0 --message ""
    echo "echo \"first commit: \${PACKAGE2_VAR:-unset}!\" > output" > build.sh
    chmod +x build.sh
    git add .
    git commit --message "Commit 2"
    git tag --annotate v2.1.0 --message ""
    git branch branch1
    echo "echo \"second commit: \${PACKAGE2_VAR:-unset}!\" > output" > build.sh
    chmod +x build.sh
    git add .
    git commit --message "Commit 3"
    git tag --annotate v2.1.1 --message ""
    cd ..
}


setup_package3() {
    mkdir package3
    cd package3
    git init
    touch f1 f2 f3
    git add .
    git commit --message "Commit 1"
    git tag --annotate v1.0.0 --message ""
    cat > Package.json <<EOF
{
    "dependencies": [
        { "repo": "../package1",
          "tag": "v1.*" },
        { "repo": "../package2",
          "tag": "v2.1.*",
          "commands": {
              "build": "./build.sh"
          },
          "env": { "PACKAGE2_VAR": "set" } }
    ],
    "commands": {
        "build": "echo \"building package 3\" > output"
    }
}
EOF
    git add .
    git commit --message "Commit 2"
    git tag --annotate v2.0.0 --message ""
    cd ..
}


setup_package4() {
    mkdir package4
    cd package4
    git init
    touch f1 f2
    git add .
    git commit --message "Commit 1"
    git tag --annotate v3.0.0 --message ""
    cat > Package.json <<EOF
{
    "dependencies": [
        { "repo": "../package2",
          "ref": "branch1",
          "commands": {
              "build": "./build.sh"
          } },
        { "repo": "../package3",
          "tag": "v2.*" }
    ],
    "commands": {
        "build": "echo \"building package 4\" > output"
    }
}
EOF
    git add .
    git commit --message "Commit 2"
    git tag --annotate v3.0.1 --message ""
    cd ..
}


main() {
    setup_package1
    setup_package2
    setup_package3
    setup_package4
}


main "$@"

