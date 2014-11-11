
**gitdep** manages the dependencies of Git projects.

Each project puts a `Dependencies.json` file in its top directory to specify its dependencies:

``` json
{
    "dependencies": [
        { "https://github.com/mcinglis/libcommon.git": "1" }
        { "url":      "https://github.com/mcinglis/libstring.git",
          "checkout": "feature/format",
          "path":     "libstring03" }
    ],
    "dev-dependencies": [
        { "https://github.com/mcinglis/libtest.git": "3" }
    ]
}
```

Then, executing `gitdep install` within your project will clone all of the specified dependencies into `dependencies/` (within the top directory of the project), check out the specified versions, and then install *their* dependencies too.

This way, you needn't specify your dependencies' dependencies, because `gitdep` handles it all.

---

Installs dependencies specified as Git projects, and those projects'
dependencies too.

1. Reads the `Dependencies.json` file in the given directory path (which we'll
call `$top`). A `Dependencies.json` file looks like:

    {
        'dependencies': [
            { 'url': 'https://github.com/mcinglis/libcommon.git',
              'tag': 'v1.*' },
            { 'url': 'git@gitorious.org:rainbow/libunicorn.git',
              'path': 'rainbow/libunicorn',
              'tag': 'v3.*' },
            { 'url': 'https://github.com/sunshine/liblollipop.git',
              'branch': 'feature/swirls' }
        ],
        'dev-dependencies': [
            { 'url': 'https://github.com/mcinglis/libtest.git'
              'commit': '2482fddefa72' }
        ]
    }

2. Clones each of the specified repositories into `$top/dependencies/$path`,
where `$path` is either specified in the `Dependencies.json` file, or is
derived from the URL akin to how `git-clone` derives the directory name.

3. Checks out the specified tag, branch or commit for each dependency.

4. Reads the `Dependencies.json` file within each dependency directory,
clones the non-development dependencies into `$top/dependencies` (the same
directory as the top-level dependencies), and checks out the specified tag,
branch or commit. This repeats until all the dependencies have been installed.

5. Creates a `Dependencies.mk` file (for GNU Make) within `$top`, which assigns
the path of each dependency to a variable named for that dependency, and
attempts to include the `Variables.mk` file in the directory of that dependency
(which can assign variables to assist with building that . The
variable name is derived from the dependency's path: '/' and '-' are replaced
with '_', and any other non-alphanumeric characters are removed. The first few
lines of a `Dependencies.mk` file created with the above `Dependencies.json`
file would be:

    libcommon = ./dependencies/libcommon
    -include $libcommon

After all the dependencies have been installed, this creates a
`Dependencies.mk` file (for GNU Make) in the given path, which assigns the path
of each dependency to a variable named for that dependency, so that dependency
paths don\'t have to be hardcoded in the Makefile. The `Dependencies.mk`.

Reads the `Package.json` file in the given directory path, clones the specified
Git URLs into a `dependencies/` folder within the given path, checks out the
appropriate commits, and repeats this process for those new packages.
