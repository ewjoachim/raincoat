# Raincoat

[![Deployed to PyPI](https://img.shields.io/pypi/v/raincoat?logo=pypi&logoColor=white)](https://pypi.org/pypi/raincoat)
[![Deployed to PyPI](https://img.shields.io/pypi/pyversions/raincoat?logo=pypi&logoColor=white)](https://pypi.org/pypi/raincoat)
[![GitHub Repository](https://img.shields.io/github/stars/ewjoachim/raincoat?style=flat&logo=github&color=brightgreen)](https://github.com/ewjoachim/raincoat/)
[![Continuous Integration](https://img.shields.io/github/actions/workflow/status/ewjoachim/raincoat/ci.yml?logo=github&branch=main)](https://github.com/ewjoachim/raincoat/actions?workflow=CI)
[![MIT License](https://img.shields.io/github/license/ewjoachim/raincoat?logo=open-source-initiative&logoColor=white)](https://github.com/ewjoachim/raincoat/blob/main/LICENSE)

_Raincoat has you covered when you can't stay DRY_. When the time comes where you HAVE
to copy/paste code from a third party into your own repo, Raincoat is a _kind of_
linter that will track if the third party gets updated, so that you can update/adjust
your local copy.

Raincoat is a tool made with Python where Python is the main usecase, but it can be used
for other stacks as well, thanks to its modular architecture.

## What is Raincoat?

### The problem

Let's say you're using a lib named `umbrella` which provides a function named
`use_umbrella` and it reads as such:

```python
def use_umbrella(umbrella):

    # Prepare umbrella
    umbrella.remove_pouch()
    umbrella.open()

    # Use umbrella
    while rain_detector.still_raining():
        umbrella.keep_over_me()

    # Put umbrella away
    umbrella.close()
    while not umbrella.is_wet():
        time.sleep(1)
    umbrella.put_pouch()
```

This function does what it says it does, but it's not ideally split, depending on your
needs. For example, maybe you want to dance with the `umbrella` when it's opened.

It's also possible that you can't really make a pull request because your needs are
specific, or you don't have the time (that's sad but, hey, I know it happens) or any
other personal reason. So what do you do? There's no real alternative. You copy/paste
the code, modify it to fit your needs and use your modified version. And whenever
there's a change to the upstream function, chances are you'll never know.

### The solution

_Enter Raincoat._

You have made your own private copy of the function `umbrella.use_umbrella` (umbrella
being at the time at version `14.5.7`) and it looks like this:

```python
def dance_with_umbrella(umbrella):
    """
    I'm siiiiiinging in the rain!
    """
    # Prepare umbrella
    umbrella.remove_pouch()
    umbrella.open()

    # Use umbrella
    while rain_detector.still_raining():
        Dancer.sing_in_the_rain(umbrella)

    # Put umbrella away
    umbrella.close()
    while not umbrella.is_wet()
        time.sleep(1)
    umbrella.put_pouch()
```

Let's add a comment to the code so that we can track it in Raincoat:

```python
# --- rainoat
# [dance_with_umbrella]
# version = "14.5.7"
# plugins = {source = "pypi", diff = "python, updater = "venv"}
# package = "umbrella"
# path = "umbrella/__init__.py"
# element = "use_umbrella"
# ---
def dance_with_umbrella(umbrella):
    """
    I'm siiiiiinging in the rain!
    """
    # ...
```

Now, install and run `raincoat` in your project:

```console
$ pip install 'raincoat[plugins]'
```

> [!NOTE]
> the `[plugins]` extra adds the dependencies for the builtin plugins, if you don't need
> them, you can just install `raincoat`)

```console
$ raincoat check
```

Raincoat will then do the following:

1. Locate the raincoat configuration comment defined above.
1. Find the current version of `umbrella` using the `venv` updater plugin.
1. If that version matches `14.5.7`, we're good.
1. If that version is different (say the current version is `16.0.3`), it will use the
   `pypi` source plugin to download the code of `umbrella` at version `14.5.7` and
   at version `16.0.3`.
1. It will then use the `python` diff plugin to compare the 2 versions of the code
   at the location specified in the `path` and `element` keys (so as to only compare
   the `use_umbrella` function).
1. If the code is identical, we're good.
1. If the code is different, it will update your comment with: `version = "16.0.3"` and
   `old_version = "14.5.7"`, and display the diff between the two versions of the code
   in your terminal.
1. Then, your role is to look at the diff, decide what to do with your code, and
   when you're done, manually remove the `old_version` line from the comment (or run
   `raincoat fix`)
1. Until you do that, running `raincoat check` will fail.

```diff
  # --- raincoat
  # [dance_with_umbrella]
  # # use_umbrella is copied and adapted in movie.singing_in_the_rain/__init__.py
  # # as dance_with_umbrella
- # version = "14.5.7"
+ # version = "16.0.3"
+ # old_version = "14.5.7" # Remove this line when the diff has been checked
  # ---
```

Of course, `raincoat` will do the above steps for all checks defined in
your codebase and in `raincoat.toml`.

## And beyond!

Actually, the base principle of Raincoat can be extended to many other topics than
PyPI packages. To fit this, Raincoat was written with a modular achitecture allowing
other kinds of Raincoat checks.

Imagine that the code you copied was from the Python standard library `Maildir._lookup`
in the file `Lib/mailbox.py` at commit `43ba8861` and you need to know if it was changed
on the master branch. What you can do is:

```toml
[maildir_lookup]
version = "43ba8861"
source.github.repo = "python/cpython"
diff.python.path = "Lib/mailbox.py"
diff.python.element = "Maildir._lookup"
updater.github_branch.branch = "main"
```

Then, when you run Raincoat, it will file `Lib/mailbox.py` from the `python/cpython`
repo at ref `43ba8861` (commit, tag or branch), look for the `Maildir._lookup` element
and compare it with the same code in the `main` branch. If the code is different, it
will tell you so, and you can update your code accordingly.

## Concepts

Raincoat is built around the concept of:

- **Source plugins**: A source plugin is responsible for locating the code of a third
  party package at a specific version.

- **Diff plugins**: A diff plugin is responsible for comparing two pieces of code
  and returning a diff result. It may scope the diff to a specific section of the code,
  such as a function or a class. If you don't specify a diff plugin, the
  `default` diff plugin will be used, which computes the full diff between the two
  pieces of code.

- **Updater plugins**: Updater plugins are responsible for determining the current
  version of the code to compare against, so as to update the version in
  `raincoat.toml`. If you don't specify an updater plugin, you'll need to manually
  call `raincoat check <check_name>=<version>` to check if the code has changed.

### The two kinds of updaters

With Raincoat, you compare the code at the "reference" version with the code at
the "new" version. There are two ways "new" can be defined:

#### Internal

Updaters may be set as "internal", this means the current version is only expected to
change in relation to something else in your project changing, such as a new version of
a dependency being set in your lock file. This is the case for the `venv` updater
plugin.

You probably want `raincoat` to check whether internal updaters report a new version
on every PR, so that you can update your code accordingly. This is what you get by
calling:

```console
$ raincoat check
```

This command will modify `raincoat.toml` or `pyproject.toml` if updaters report
new versions and the code on that new version has changed, so that you can review the
changes and update your code accordingly.

#### External

Updaters may be set as "external", this means the current version is expected to
change independently of your project, such as a new version of the upstream code being
released. This is the case for the `github-tag` and `github-branch` updater
plugins.

You probably don't want `raincoat` to check whether external updaters report a new
version on every PR, because it will likely fail on every PR if a new version has been
released upstream. Instead, you probably want `raincoat` to run periodically to check if
the version has changed, and if it has, make a PR with the changes.

You also probably want that PR's CI to fail if the code has changed, so that you
can review the changes and update your code accordingly. This is what you get by
calling:

```console
$ raincoat update
```

if updaters report new versions, this command will modify `raincoat.toml` or
`pyproject.toml`. If the code hasn't changed, it will just update the version. If the
code has changed, it will add an `old_version` attribute to the check. Following calls
to `raincoat check` will then compare the code at the `old_version` with the code at
`version`, which will fail, so that you can review the changes and update your code
accordingly.

```diff
  # --- raincoat
  # [dance_with_umbrella]
- # version = "14.5.7"
+ # version = "16.0.3"
+ # old_version = "14.5.7" # Remove this line when the diff has been checked
  # ---
```

To get the PR to pass, you will need to remove the `old_version` line. There are
ways to remove this line simply, without checking out the PR, see the "GitHub Actions"
section below.

## Reference documentation

### inline comments, `raincoat.toml`, `pyproject.toml`

Raincoat checks can be defined in a `raincoat.toml` file, or inline in your code
using comments.

#### Inline comments

Given Raincoat excepts may be introduced in non-Python files, the detection allows for
abitrary comment types. Raincoat will look for lines containing `--- raincoat`, and will
take note of the prefix of this line. Then it will look for the following lines
until it finds a line containing `---` with the same prefix. In each of those lines, the
prefix will be stripped, and the remaining text will be parsed as a TOML table.

Example:

````python
# --- raincoat
# [dance_with_umbrella]
# version = "14.5.7"
# source.pypi.package = "umbrella"
# diff.python.path = "umbrella/__init__.py"
# diff.python.element = "use_umbrella"
# updater.venv = {}
# ---
def dance_with_umbrella(umbrella):
    ...

#### `raincoat.toml`

If you want to avoid inline comments, or if there's no good place to put it in your
code, you can put the configuration in `raincoat.toml` . In that case, don't put the
`# --- raincoat` prefix and `# ---` suffix.
Also, the table should be nested in a `checks` section, like this:

```toml
[checks.dance_with_umbrella]
version = "14.5.7"
location = "umbrella/__init__.py"
source.pypi.package = "umbrella"
diff.python.path = "umbrella/__init__.py"
diff.python.element = "use_umbrella"
updater.venv = {}
````

When a check is defined inline, its `location` is the file where the check is defined.
When it's defined in `raincoat.toml`, it has no default `location`. You may provide a
`location` as an arbitrary string that will be displayed in the error message when the
check fails.

#### `pyproject.toml`

It's also possible to put it in `pyproject.toml`. It works the same way as
`raincoat.toml`, you'll have to nest sections within `tool.raincoat` (with the `checks`):

```toml
# pyproject.toml
[tools.raincoat.checks.dance_with_umbrella]
# ...
```

### Check configuration structure

Each raincoat check configuration looks like:

```toml
[...{check_name}]
version = "str"
update_if_no_diff = true
source.{source_plugin_name}.{...} = ...
diff.{diff_plugin_name}.{...} = ...
updater.{updater_plugin_name}.{...} = ...
```

Where:

- `check_name` may be prefixed, as explained above:
  - `[check_name]` if in an inline comment
  - `[checks.check_name]` if in `raincoat.toml`
  - `[tool.raincoat.checks.check_name]` if in `pyproject.toml`
- `version` (mandatory): a string representation of the current version
- `update_if_no_diff` (optional, default `true`): if true, the comment will be updated to the newest version even when there's no diff to report
- `source.{source_plugin_name}.{...}`: (mandatory): source plugin name and configuration keys
- `diff.{diff_plugin_name}.{...}`: (optional): diff plugin name and configuration keys. If not present, defaults to plugin named `default` that does a simple textual diff between the 2 full sources.
- `updater.{updater_plugin_name}.{...}`: (optional): update plugin name and configuration keys. If not present, this check can only be updated manually.

### Builtin plugins & future ideas

#### Builtin source plugins

##### `pypi`

This plugin locates the code of a third party package on PyPI, at a specific version.

##### `github`

This plugin locates the code of a third party package on GitHub, at a specific commit,
branch or tag.

##### Other ideas

One may implement other source plugins, such as:

- `git` or other VCS (more generic than GitHub but may require more configuration)
- Other package managers (e.g. `npm`, `cargo`, `composer`, etc.)

#### Builtin diff plugins

##### `default`

This plugin computes the full diff between two pieces of code, without scoping it to
a specific section of the code.

##### `python`

Compares two pieces of Python code (scope might be a whole module or a single function/class/method).
If the ASTs of the two pieces of code are identical, it will report they're identical even if
the code is formatted differently.

##### Other ideas

One may implement other diff plugins, such as:

- Any other language (e.g. `typescript`, `rust`, etc.)

#### Builtin updater plugins

##### `venv`

Reports the currently installed version of a package in the current virtualenv.

##### `github-tag`

Reports the latest tag of a repository on GitHub. You can use `remove_v_prefix=true` (it's the default value) if
the project's tags are prefixed with `v` (e.g. `v1.2.3`) and the source plugin takes
PEP-440 version strings (e.g. `1.2.3`).

##### `github-branch`

Reports the latest commit hash of a branch on GitHub. You can specify a branch to use
(`branch="main"`) or let it default to the repository's default branch.

#### Other ideas

One may implement other version plugins, such as:

- lock file parser (e.g. `uv.lock`, `poetry.lock`, etc.)
- git: might be useful for git repository that are not on GitHub

### Creating your own custom Raincoat plugins

Source, Diff and Updater plugins are registered using entry points, you may
familiarize yourself with how those work in your Python package manager of choice.

- [PEP-621 compatible tool (setuptools, uv, hatch, ...)](https://setuptools.pypa.io/en/latest/userguide/entry_point.html#entry-points-for-plugins)
- [poetry](https://python-poetry.org/docs/pyproject/#entry-points)

The entry points are registered under the `raincoat.source`, `raincoat.diff` and
`raincoat.updater` namespaces, respectively.

Example (PEP-621):

```toml
# pyproject.toml
[project]
# ...

[project.entry-points]
"raincoat.source".my_source_plugin_name = "dotted.path.to.module:callable_name"
"raincoat.diff".my_diff_plugin_name = "dotted.path.to.module:callable_name"
"raincoat.updater".my_updater_plugin_name = "dotted.path.to.module:callable_name"
```

#### Source plugins

Source plugins receive their configuration dict from `raincoat.toml` file, that
includes a list of checks, and are responsible for locating the 2 versions of the code
to compare.

At core, a source plugin is a _callable_ (usually a function, or an object that has a
`__call__` method) with the following signature:

```python
def source_plugin(*, version: str, **config: Any) -> str:
    """
    A source plugin locates the code of a third party package at a specific version.

    Parameters
    ----------
    version:
        The version of the code to locate
    config:
        The configuration dict for the source section of the check parsed
        from `raincoat.toml`.

    Returns
    -------
    The code, as a string.
    """
```

Example of a source plugin for a Rust crate:

```python
import tarfile

def rust_crate(*, version: str, crate: str, filename: str) -> str:
    with httpx.Client() as client:
        response = client.get(
            f"https://static.crates.io/crates/{crate}/{crate}-{version}.crate"
        )
        response.raise_for_status()
        content = response.aread()

    with tarfile.open(fileobj=io.BytesIO(content)) as tar:
        # Extract the file from the tar archive
        member = tar.getmember(filename)
        return tar.extractfile(member).read().decode("utf-8")
```

Corresponding `raincoat` configuration example:

```toml
[foo]
version = "3.2.7"
source.rust_crate.crate = "some_crate"
source.rust_crate.filename= "src/lib.rs"
```

#### Diff plugins

Diff plugins are responsible for comparing 2 code strings, potentially scoping the diff
to a specific section of the code, and returning a string explaining the difference, or
`None` if they're identical.

```python
def diff_plugin(*, ref: str, new: str, **config: Any) -> str | None:
    """
    A diff plugin computes the diff between two versions of the same code, potentially
    scoping the diff to a specific section of the code.

    Parameters
    ----------
    ref:
        The reference code to compare against.
    new:
        The new code to compare with the reference code.
    config:
        The configuration dict for the diff section of the check parsed
        from `raincoat.toml`.

    Returns
    -------
    The diff as a string, or `None` if the two pieces of code are functionally identical.
    """
```

```python
import difflib

def diff_between(*, ref: str, new: str, after: str, before: str) -> str | None:
    """
    A diff plugin that compares two code strings, scoped between the first occurrence
    of `after` and the subsequent occurrence of `before`.
    """

    scoped_ref = ref.split(after, 1)[-1].split(before, 1)[0]
    scoped_new = new.split(after, 1)[-1].split(before, 1)[0]

    if scoped_ref == scoped_new:
        return None

    # Use difflib to compute the diff
    return ''.join(
        difflib.unified_diff(
            scoped_ref.splitlines(keepends=True),
            scoped_new.splitlines(keepends=True),
            fromfile="ref",
            tofile="new",
        )
    )
```

Corresponding `raincoat` configuration example:

```toml
[foo]
version = "3.2.7"
source.rust_crate.crate = "some_crate"
source.rust_crate.filename= "src/lib.rs"
diff.between.after = "fn foo("
diff.between.before = "\n}"
```

#### Updater plugins

Updater plugins are responsible for determining the new version of the code to
compare against, so as to update the version in `raincoat.toml`. They receive the
configuration dict for the check parsed from `raincoat.toml` and are expected to return
the current version of the code as a string.

Updater plugins often need the same configuration as the source plugin, so they
will recieve merged configuration from both the source section and the updater
section. They are expected to accept `**kwargs`, so that they can be used with
different configurations.

```python
def updater_plugin(**config: Any) -> str:
    """
    An updater plugin determines the current version of the code to compare against.

    Parameters
    ----------
    config:
        The configuration dict for the check parsed from `raincoat.toml`.
        If the configuration includes elements from both the source and updater section,
        merged together with the updater section taking precedence.

    Returns
    -------
    The current version of the code as a string.
    """
```

```python
import httpx

def github_latest_tag(*, repo: str, **kwargs) -> str:
    """
    An updater plugin that fetches the latest tag of a GitHub repository.
    """
    with httpx.Client() as client:
        response = client.get(f"https://api.github.com/repos/{repo}/tags")
        response.raise_for_status()
        latest_tag = (response.json())[0]["name"]
        return latest_tag
```

Corresponding `raincoat` configuration example:

```toml
[foo]
version = "3.2.7"
source.github.repo = "some/repo"
updater.github_latest_tag = {}
```

##### External updaters

By default, updater plugins are "internal", meaning they are considered to only detect
a new version if _something in your project changes_, such as a new version of a
dependency being set in your lock file. These updaters can run in the CI on every
PR, and won't randomly fail solely because upstream code has a new version.

If you want to declare your updater plugin as "external", meaning it will update the
latest avaliable version of its project, then you should provide a callable that has the
`external` attribute set to `True`. The recommanded way of doing that is to use the
`@raincoat.external`. In our example above, the `github_latest_tag` updater plugin
should be declared as external, like this:

```python
import httpx
import raincoat

@raincoat.external
def github_latest_tag(*, repo: str, **kwargs) -> str:
    ...
```

> [!NOTE]
> You could also do it "the ugly way", by setting the `external` attribute
> manually (and your type-checker will likely complain about it):
>
> ```python
> import httpx
>
> def github_latest_tag(*, repo: str, **kwargs) -> str:
>     ...
> github_latest_tag.external = True
> ```

### Github Actions

TODO!

### Pre-commit hooks

You can use Raincoat as a pre-commit hook to check if the code has changed before
committing. This will only check the internal updaters. To do so, you can add the
following to your `.pre-commit-config.yaml` file:

```yaml
repos:
  # ...
  - repo: "https://github.com/ewjoachim/raincoat"
    rev: "x.y.z" # Use the latest version
    hooks:
      - id: raincoat
```

## Discussions

### Caveats and Gotchas

- Raincoat doesn't analyze what you've put in your code, so it doesn't matter _what_
  you actually do with the code you want to track: whether you copy/paste it, or port
  it to another language, or even if you just use it as a reference, Raincoat just
  track the upstream code.
- Raincoat's builtin plugins don't run upstream code. That said, external plugins might
  do do.
- We recommand against running external updaters on every PR, as they will
  likely fail if a new version has been released upstream.

### v2?

Raincoat was created in 2016 and left dormant for a long time. It was revived in 2025,
redesigned and rewritten from the ground up, and given how (retrospectively) bad (IMHO)
some of _my_ initial design decisions were, it felt like completely breaking
compatibility with the previous version was a once-in-a-decade acceptable thing to do.

If you knew Raincoat before v2, congratulations, you're a long-time fan!

### Inline comments and PEP-723

You'll notice that the inline comment format looks similar to the one defined by
PEP-723, but it's not the same: Raincoat uses `---` instead of `///` to delimit
blocks, allows multiple `raincoat` blocks in the same file and allows comments to
be indented. Also, PEP-723 explicitly forbids the introduction of custom blocks types,
so Raincoat's inline comments could never be PEP-723 compliant. Instead, Raincoat
uses its own format, which is similar to PEP-723 but distinct.

## Acknowledgments

This code is based on an idea we got at [Smart Impulse](http://smart-impulse.com)
around 2014. Kudos to them.

```

```
