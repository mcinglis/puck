
**Puck** is a tool for recursively downloading a project's dependencies specified as Git repository URLs, and for applying "commands" to each of those dependencies. You can use it for decoupling a project from the dependencies of its own dependencies, and from the build process (if any) of its dependencies.

Puck requires little buy-in; packages can be used as dependencies without having a `Package.json` file of their own. Puck is small and purpose-built. Puck is based on a decentralized model, so you can easily meld it to your requirements.



## How it works

Puck finds and parses a `Package.json` file (per [`package-schema.json`](package-schema.json)) in the package's root directory, which holds a JSON object representing the dependencies of that package, and how to handle commands issued to it when it is used as a dependency.


### `puck update`

**In short:** Puck reads the root package's `Package.json`, clones its dependencies into the `deps` directory, and repeats that process for each of its dependencies (but downloading their dependencies into the root `deps` directory)  until all dependencies (and their dependencies, and theirs, ...) have been retrieved. While the root package is required to have a `Package.json` file, the dependencies do not.

**In detail:** Puck looks at each of the specified dependency objects, and:

- If the object has a `"path"` member, it is used as the dependency's *path*. Otherwise, the *path* is derived from the `"repo"` member similar to how Git derives the folder name from a repository URL. For example, with `"repo"` equal to "git@bitbucket.org:fake456/libcat.git" the dependency's *path* will be `libcat`.

- If a dependency has already been updated at this dependency's path, and they do not share the exact same configuration (version, environment, etc), then this is a dependency conflict, an error message is printed accordingly, and Puck stops updating. If they do share the same configuration, then Puck moves onto updating the next dependency if any, because it's already updated that dependency.

- If a directory does not exist at `deps/<path>` within the root directory of the project, the repository is cloned to that path. If a directory does exist that path, then the latest changes are fetched into it.

- The repository is checked out to the specified tag or reference (if any):

  - If a tag pattern is specified via the `"tag"` field in the object, then the highest tag matching that pattern is chosen (e.g. so `v2.2.1 > v2.2.0 > v2.1.0`), and the GPG signature on that tag is verified. You'll need the tagger's GPG key on your keychain for verification to work. If you don't want to verify the tag, pass the `--no-verify` argument to `puck update`. After verification, the tag is checked out.

  - Otherwise, if a reference string is specified via the `"ref"` field in the object, then Puck simply checks out that reference (e.g. `git checkout <ref>`).

  - Otherwise, the repository is left as-is.

- If a `Package.json` file is in the dependency's directory, then this dependency's listed dependencies are also updated into the root `deps` directory.

Puck does not detect and remove garbage dependencies - repositories that were once a dependency, but no longer. You could get rid of those by something like `rm -rf deps && puck update`.


### `puck execute foo`

**In short:** the command "foo" is executed in a depth-first traversal of the dependency tree. How a particular dependency responds to the "foo" command is specified in its `Package.json`: one dependency may be built with GNU Make, another with shell scripts, and one may not even require building. A command is only issued to a dependency once in the entire traversal, even if that dependency has multiple parents in the dependency tree.

**In detail:** for each of the specified dependency objects in the `Package.json`, Puck extracts the path of the dependency as described in the previous section, then reads `deps/<path>/Package.json` (if any). From that:

- Executes the given command "foo" in each dependency directory as mentioned in the following step, skipping dependencies for which the command has already been issued (e.g. from different branches of the dependency tree).

- Executes the given command "foo" in this dependency directory by:

  - If `"foo"` is a member of the `"commands"` object of the dependency's `Package.json` object, then the corresponding value string is executed as a subprocess with the working directory set to the dependency's directory, and with the `DEPS_DIR` environment variable being set to the path of the `deps` directory within the root package.

  - Otherwise, a message is printed signalling that no handler for the `foo` command was found.

Conventional command names to specify in your `Package.json` file are `build`, `test`, and `clean`.


## Releases

I'll tag the releases according to [semantic versioning](http://semver.org/spec/v2.0.0.html). All the modules and identifiers are considered part of the public interface, so breaking changes to those things should only happen between major versions. Backwards-compatible additions will happen between minor versions.

Every version tag will be signed with [my GPG key](http://pool.sks-keyservers.net/pks/lookup?op=vindex&search=0xD020F814) (fingerprint: `0xD020F814`).



## Collaboration

Puck is available at [Gitorious](https://gitorious.org/mcinglis/puck), [Bitbucket](https://bitbucket.org/mcinglis/puck), and [GitHub](https://github.com/mcinglis/puck).

Questions, discussion, bug reports and feature requests are welcome at [the GitHub issue tracker](https://github.com/mcinglis/puck/issues), or via [emails](mailto:me@minglis.id.au).

To contribute changes, you're welcome to [email me](mailto:me@minglis.id.au) patches as per `git format-patch`, or to send me a pull request on any of the aforementioned sites. You're also welcome to just send me a link to your remote repository, and I'll merge stuff from that as I want to.

To accept notable contributions, I'll require you to assign your copyright to me. In your email/pull request and commit messages, please insert: "*I hereby irrevocably transfer to Malcolm Inglis (http://minglis.id.au) all copyrights, title, and interest, throughout the world, in these contributions to Puck*". If you can, please sign the email or pull request, ensuring your GPG key is publicly available.


## License

**Copyright 2014 Malcolm Inglis <http://minglis.id.au>**

Puck is free software: you can redistribute it and/or modify it under the terms of the [GNU Affero General Public License](https://gnu.org/licenses/agpl.html) as published by the [Free Software Foundation](https://fsf.org), either version 3 of the License, or (at your option) any later version.

Puck is distributed in the hope that it will be useful, but **without any warranty**; without even the implied warranty of **merchantability** or **fitness for a particular purpose**. See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along with Puck. If not, see <https://gnu.org/licenses/>.

[Contact me](mailto:me@minglis.id.au) for proprietary licensing options.

### Why AGPL?

[I believe that nonfree software is harmful](http://minglis.id.au/blog/2014/04/09/free-software-free-society.html), and I don't want to contribute to its development at all. I believe that a free society must necessarily operate on free software. I want to encourage the development of free software, and discourage the development of nonfree software.

The [GPL](https://gnu.org/licenses/gpl.html) was designed to ensure that the software stays free software; "to ensure that every user has freedom". The GPL's protections may have sufficed in 1990, but they don't in 2014. The GPL doesn't consider users of a web service to be users of the software implementing that server. Thankfully, the AGPL does.

The AGPL ensures that if Puck is used to implement a web service, then the entire source code of that web service must be free software. This way, I'm not contributing to nonfree software, whether it's executed locally or provided over a network.


