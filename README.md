
**Puck** is a tool for downloading a project's dependencies (and sub-dependencies), and for applying "commands" to each of those dependencies. You can use it for decoupling a project from the dependencies of its own dependencies, and from the build process (if any) of its dependencies.

Puck requires little buy-in; packages can be used as dependencies without having a `Package.json` file of their own. Puck is small and purpose-built, and has an accessible API. Puck is based on a decentralized model, so you can easily meld it to your requirements.

Puck currently only works with Git repositories, but it has been modelled and documented to be agnostic as to what distributed version control system is used.

![puck](https://raw.githubusercontent.com/mcinglis/puck/master/puck.jpg) *RWWEEAARR*



## How it works

Puck finds and parses a `Package.json` file in the package's root directory, which holds a JSON object representing the dependencies of that package, and how to handle commands issued to it.


### `puck update`

**In short:** Puck reads the root package's `Package.json`, gets its dependencies into the `deps` directory, reads their `Package.json`s (if any), and gets their dependencies into the `deps` directory. It repeats this process recursively until all dependencies have been retrieved. Duplicate dependencies are skipped, and conflicting dependencies are detected and reported.

**In detail:** Puck looks at each of the specified dependency objects, and:

- If the object has a `"path"` member, it is used as the dependency's *path*. Otherwise, the *path* is derived from the `"repo"` member and `"tag"` member if it looks something like `v1.*` or `v5.12.*` or `v9.1.2` (i.e. [semantic versioning](http://semver.org). For example, with `"repo"` equal to "git@bitbucket.org:fake456/libcat.git" and `"tag"` equal to `"v2.5.*"`, the dependency's *path* will be `libcat-2.5`.

- If a directory does not exist at `deps/<path>` within the root directory of the project, the repository is cloned to that path. If a directory does exist that path, then the latest changes are fetched into it.

- The repository is checked out to the specified tag or reference (if any):

  - If a tag pattern is specified via the `"tag"` field in the object, then the highest tag matching that pattern is chosen (e.g. so `v2.2.1 > v2.2 > v2.1`), and the GPG signature on that tag is verified. You'll need the tagger's GPG key on your keychain for verification to work. If you don't want to verify the tag, pass the `--no-verify` argument to `puck update`. After verification, the tag is checked out.

  - Otherwise, if a reference string is specified via the `"ref"` field in the object, then Puck simply checks out that reference (e.g. `git checkout <ref>`).

  - Otherwise, the repository is left as-is.

- If a `Package.json` file is in the dependency's directory, then that file is read and parsed as per the root package's `Package.json`. Then, the dependency's dependencies are fetched just as if `puck update` were executed in its directory,  except that equivalent dependencies to those already fetched are skipped, conflicting dependencies (same path but different repository url / version / environment) are checked, and its dependencies are downloaded to the `deps` directory of the root package.

Puck does not detect and remove garbage dependencies - repositories that were once a dependency, but no longer. You must manually address those, or simply run `puck clean && puck update`.


## `puck execute foo`

**In short:** the command "foo" is executed in a depth-first traversal of the dependency tree as described in the previous section. How a particular dependency responds to the "foo" command is specified in its `Package.json`: one dependency may be built with GNU Make, another with shell scripts, and one may not even require building. A command is only issued to a dependency once in the entire traversal, even if that dependency has multiple parents in the dependency tree.

**In detail:** for each of the specified dependency objects in the `Package.json`, Puck extracts the path of the dependency as described in the previous section, then reads `deps/<path>/Package.json` (if any). From that:

- Executes the given command "foo" in each dependency directory as mentioned in the following step, skipping dependencies for which the command has already been issued (e.g. from different branches of the dependency tree).

- Executes the given command "foo" in this dependency directory by:

  - If `"foo"` is a member of the `"commands"` object of the dependency's `Package.json` object, then the corresponding value string is executed as a subprocess with the working directory set to the dependency's directory, and with the `DEPS_DIR` environment variable being set to the path of the `deps` directory within the root package.

  - Otherwise, a message is printed signalling that no handler for the `foo` command was found.

Conventional command names to specify in your `Package.json` file are `build`, `test`, and `clean`.


## Example

Suppose we are developing a project that requires Antifier v1, Libbear on the `feature-claws` branch (obtainable on a network file system) and built via `make fast`, and, for development, Libcat v2.5 built with the `LIBCAT_CUTENESS` environment variable set to `9001`. Suppose that Antifier v1 depends on Libbear v3 and Libdog v1. Libdog v1 depends on Libcat v2 (without the `LIBCAT_CUTENESS` value set as per the root project's dependency).

The authors of our depedencies had the prescience to stick to [semantic versioning](http://semver.org). This means we don't need to be stuck on specific versions: we can simply require a major version of a package via a tag pattern, and let Puck get us the highest minor and patch versions under that major version.

Our root project will be using `make` as the build tool, with a makefile having `build`, `test` and `clean` targets. We want to expose this functionality so that the root project can be easily used as a dependency in Puck.

For the project, we would write a `Package.json` file like:

``` json
{
    "dependencies": [

        { "repo": "https://gitorious.org/fake123/antifier.git",
          "tag":  "v1.*" },

        { "repo": "/mnt/team-grizzly/libbear",
          "ref":  "feature-claws",
          "path": "libbear-claws",
          "commands": { "build": "make fast" } },

        { "repo": "git@bitbucket.org:fake456/libcat.git",
          "tag":  "v2.5.*",
          "env":  { "LIBCAT_CUTENESS": "9001" },
          "dev":  true }

    ],

    "commands": {
        "build": "make",
        "test":  "make test",
        "clean": "make clean"
    }
}
```

See [package-schema.json](package-schema.json) for a formal specification of `Package.json` files as per [JSON Schema](http://json-schema.org/).



### `puck update`

Running `puck update` for the first time in a project having the example `Package.json` above:

- the Antifier repository URL will be cloned to `deps/antifier-1`, and it will be checked out to tag `v1.3.2`, because that is the highest tag matching the given pattern `v1.*`. Antifier at tag `v1.3.2` has its own `Package.json` specifying its own dependencies. So then:

  - Libbear will be cloned from the URL specified in Antifier's `Package.json`, and will be checked out to `v3.0`, because that is the highest tag matching the pattern `v3.*` given by Antifier's `Package.json`. Libbear at `v3.0` has no `Package.json`, so Puck moves onto the next dependency of Antifier.

  - Libdog will be cloned from the URL specified in Antifier's `Package.json`, and will be checked out to `v1.7.1`, because that is the highest tag matching the pattern `v1.*` given by Antifier's `Package.json`. Libdog at `v1.7.1` has a `Package.json`, so then:

    - Libcat will be cloned from the URL specified in Libdog's `Package.json`, and will be checked out to `v2.2` because that is the highest tag matching the pattern `v2.*` given by Libdog's `Package.json`. 





- the Libpp repository URL will be cloned to `deps/libpp-14`, and it will be checked out to commit `5e562d`. Libpp doesn't have a `Package.json` file in that commit, so it is treated as having no dependencies.

- the Libmacro repository URL will be cloned to `deps/libmacro`, the available tags matching `v2.*` will be listed, and the highest matching tag, `v2.0`, is chosen. This tag is verified, and then checked out. Libmacro's `Package.json` is then parsed, and its dependencies are installed. Libmacro at that version depends on Libpp at `v2.*` and Libtypes at `v2.*`. Thus:

  - Libmacro's specified URL for Libpp is cloned to `deps/libpp`, and tag `v2.1.1` is verified and checked out. Libpp has no `Package.json` at that version, which Puck takes to mean as having no dependencies.

  - Libmacro's specified URL for Libtypes is cloned to `deps/libtypes`, and tag `v2.0` is verified and checked out. Libtypes has no `Package.json` at that version, which Puck takes to mean as having no dependencies.

All dependencies have thus been updated.



### Example

Running `puck execute build` in a project having the example `Package.json` above:

- In `deps/libpp-14`, there is no `Package.json`, thus there are no handlers for "build".

- In `deps/libpp`, there is a `Package.json` with no `"commands"` member, but with a `"command-delegate"` member set to `"make"`. Thus, the command `make build` is executed in `deps/libpp`, with the `DEPS_DIR` environment variable set to the absolute path of `deps`.

- In `deps/libtypes` (a dependency of the root's Libmacro dependency), there is no `Package.json`, thus there are no handlers for "build".

- In `deps/libmacro`, there is a `Package.json` with no `"commands"` member, but with a `"command-delegate"` member set to `"make"`. Thus, the command `make build` is executed in `deps/libmacro`, with the `DEPS_DIR` environment variable set to the absolute path of `deps`.

You can pass `--root` to `puck execute` to also execute the given command in the root package after the dependency packages.



## Releases

I'll tag the releases according to [semantic versioning](http://semver.org/spec/v2.0.0.html). All the modules and identifiers are considered part of the public interface, so breaking changes to those things should only happen between major versions. Backwards-compatible additions will happen between minor versions.

Every version tag will be signed with [my GPG key](http://pool.sks-keyservers.net/pks/lookup?op=vindex&search=0xD020F814) (fingerprint: `0xD020F814`).



## Collaboration

Puck is available at [Gitorious](https://gitorious.org/mcinglis/puck), [Bitbucket](https://bitbucket.org/mcinglis/puck), and [GitHub](https://github.com/mcinglis/puck).

Questions, discussion, bug reports and feature requests are welcome at [the GitHub issue tracker](https://github.com/mcinglis/puck/issues), or via [emails](mailto:me@minglis.id.au).

To contribute changes, you're welcome to [email me](mailto:me@minglis.id.au) patches as per `git format-patch`, or to send me a pull request on any of the aforementioned sites. You're also welcome to just send me a link to your remote repository, and I'll merge stuff from that as I want to.

To accept notable contributions, I'll require you to assign your copyright to me. In your email/pull request and commit messages, please insert: "*I hereby irrevocably transfer to Malcolm Inglis (http://minglis.id.au) all copyrights, title, and interest, throughout the world, in these contributions to Puck*". If you can, please sign the email or pull request, ensuring your GPG key is publicly available.


