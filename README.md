# raincoat

[![Deployed to PyPI](https://img.shields.io/pypi/v/raincoat?logo=pypi&logoColor=white)](https://pypi.org/pypi/raincoat)
[![Deployed to PyPI](https://img.shields.io/pypi/pyversions/raincoat?logo=pypi&logoColor=white)](https://pypi.org/pypi/raincoat)
[![GitHub Repository](https://img.shields.io/github/stars/ewjoachim/raincoat?style=flat&logo=github&color=brightgreen)](https://github.com/ewjoachim/raincoat/)
[![Continuous Integration](https://img.shields.io/github/actions/workflow/status/ewjoachim/raincoat/ci.yml?logo=github&branch=main)](https://github.com/ewjoachim/raincoat/actions?workflow=CI)
[![MIT License](https://img.shields.io/github/license/ewjoachim/raincoat?logo=open-source-initiative&logoColor=white)](https://github.com/ewjoachim/raincoat/blob/main/LICENSE)

_Raincoat has you covered when you can't stay DRY_. When the time comes where you HAVE
to copy/paste code from a third party into your own repo, Raincoat is a kind of
linter that will track if the third party gets updated, so that you can update/adjust
your local copy.

Raincoat is a tool made with Python where Python is the main usecase, but it can be used
for other stacks as well, thanks to its modular architecture.

# What is Raincoat?

## The problem

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

## The solution

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

Now in `raincoat.toml`, add a section like this:

```toml
[checks.dance_with_umbrella]
# use_umbrella is copied and adapted in movie.singing_in_the_rain/__init__.py
# as dance_with_umbrella
version = "14.5.7"

[checks.dance_with_umbrella.source.pypi]
package = "umbrella"

[checks.dance_with_umbrella.diff.python]
path = "umbrella/__init__.py"
element = "use_umbrella"

[checks.dance_with_umbrella.updater.venv]
```

Now, install and run `raincoat` in your project:

```console
$ pip install raincoat
$ raincoat
```

It will read `raincoat.toml`, and:

1. Find the current version of `umbrella` using the `venv` updater plugin.
2. If that version matches `14.5.7`, we're good.
3. If that version is different (say the current version is `16.0.3`), it will use the
   `pypi` source plugin to download the code of `umbrella` at version `14.5.7` and
   at version `16.0.3`.
4. It will then use the `python` diff plugin to compare the 2 versions of the code
   at the location specified in the `path` and `element` keys (so as to only compare
   the `use_umbrella` function).
5. If the code is identical, it will rewrite the `raincoat.toml` file to update
   the version to `16.0.3`
6. If the code is different, it will error out and tell you that the code has changed
   and you should update your code accordingly. It will show you the diff.
7. Then, your role is to look at the diff, decide what to do with your code, and
   when you're done, update the version in `raincoat.toml` to `16.0.3` manually.

```diff
  [checks.dance_with_umbrella]
  # use_umbrella is copied and adapted in movie.singing_in_the_rain/__init__.py
  # as dance_with_umbrella
- version = "14.5.7"
+ version = "16.0.3"
```

Of course, `raincoat` will do the above steps for all checks defined in
`raincoat.toml`.

Raincoat can be used like a linter, you can integrate it in CI.

## And beyond!

Actually, the base principle of Raincoat can be extended to many other topics than
PyPI packages. To fit this, Raincoat was written with a modular achitecture allowing
other kinds of Raincoat checks.

Imagine that the code you copied was from the Python standard library `Maildir._lookup`
in the file `Lib/mailbox.py` at commit `43ba8861` and you need to know if it was changed
on the master branch. What you can do is:

```toml
[checks.maildir_lookup]

version = "43ba8861"

[checks.maildir_lookup.source.github]
repo = "python/cpython"

[checks.maildir_lookup.diff.python]
path = "Lib/mailbox.py"
element = "Maildir._lookup"

[checks.maildir_lookup.updater.github]
branch = "main"
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
  call `raincoat update <check_name> <version>` to check if the code has changed.

## Reference documentation

### `raincoat.toml`

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

#### Builtin version plugins

##### `venv`

Reports the currently installed version of a package in the current virtualenv.

##### `github`

Reports the latest version of a package on GitHub. If used without parameters, it will
use the default branch of the repository. You can specify a branch to use
(`branch="main"`) or use tags (`latest_tag=true`). When using tags, you can use
`remove_v_prefix=true` if the project's tags are prefixed with `v` (e.g. `v1.2.3`)
and the source plugin takes PEP-440 version strings (e.g. `1.2.3`).

#### Other ideas

One may implement other version plugins, such as:

- lock file parser (e.g. `uv.lock`, `poetry.lock`, etc.)
- git: might be useful for git repository that are not on GitHub

### Creating your own custom Raincoat plugins

Source, Diff and Updater plugins are registered using entry points, you may
familiarize yourself with how those work in your Python package manager of choice.

- [PEP-621 compatible tool (setuptools, uv, hatch, ...)](https://setuptools.pypa.io/en/latest/userguide/entry_point.html#entry-points-for-plugins)
- [poetry](https://python-poetry.org/docs/pyproject/#entry-points)

Example (PEP-621):

```toml
# pyproject.toml
[project]
# ...

[project.entry-points."raincoat.source"]
my_source_plugin_name = "dotted.path.to.module:callable_name"

[project.entry-points."raincoat.diff"]
my_diff_plugin_name = "dotted.path.to.module:callable_name"

[project.entry-points."raincoat.updater"]
my_updater_plugin_name = "dotted.path.to.module:callable_name"
```

#### Source plugins

Source plugins receive their configuration dict from `raincoat.toml` file, that
includes a list of checks, and are responsible for locating the 2 versions of the code
to compare.

At core, a source plugin is a _callable_ (usually a function, or an object that has a
`__call__` method) with the following signature:

```python
def source_plugin(version: str, **config: Any) -> str:
    """
    A source plugin locates the code of a third party package at a specific version.

    Parameters
    ----------
    version:
        The version of the code to locate
    config:
        The configuration dict for the check parsed from `raincoat.toml`.

    Returns
    -------
    The code, as a string.
    """
```

Example of a source plugin for a Rust crate:

```python
import tarfile

def rust_crate(version: str, crate: str, filename: str) -> str:
    response = httpx.get(
        f"https://static.crates.io/crates/{crate}/{crate}-{version}.crate"
    )
    response.raise_for_status()
    with tarfile.open(fileobj=io.BytesIO(response.content)) as tar:
        # Extract the file from the tar archive
        member = tar.getmember(config["filename"])
        return tar.extractfile(member).read().decode("utf-8")
```

Corresponding `raincoat.toml` configuration:

```toml
[checks.foo]
version = "3.2.7"

[checks.foo.source.rust_crate]
crate = "some_crate"
filename= "src/lib.rs"
```

#### Diff plugins

Diff plugins are responsible for comparing 2 code strings, potentially scoping the diff
to a specific section of the code, and returning a string explaining the difference, or
`None` if they're identical.

```python
def diff_plugin(ref: str, new: str, **config: Any) -> str | None:
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
        The configuration dict for the check parsed from `raincoat.toml`.

    Returns
    -------
    The diff as a string, or `None` if the two pieces of code are functionally identical.
    """
```

```python
import difflib

def diff_between(ref: str, new: str, after: str, before: str) -> str:
    """
    A diff plugin that compares two code strings, scoped between the first occurrence
    of `after` and the subseqyent occurrence of `before`.
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

Corresponding `raincoat.toml` configuration:

```toml
[checks.foo]
version = "3.2.7"

[checks.foo.source.rust_crate]
crate = "some_crate"
filename= "src/lib.rs"

[checks.foo.diff.python]
after = "fn foo("
before = "\n}"
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

def github_latest_tag(repo: str, **kwargs) -> str:
    """
    An updater plugin that fetches the latest tag of a GitHub repository.
    """
    response = httpx.get(f"https://api.github.com/repos/{repo}/tags")
    response.raise_for_status()
    latest_tag = response.json()[0]["name"]
    return latest_tag
```

Corresponding `raincoat.toml` configuration:

```toml
[checks.foo]
version = "3.2.7"

[checks.foo.source.github]
repo = "some/repo"

[checks.foo.diff.python]
after = "def foo("
before = "\n}"

[checks.foo.updater.github_latest_tag]
```

## Discussions

### Caveats and Gotchas

- Raincoat doesn't analyze what you've put in your code, so it doesn't matter _what_
  you actually do with the code you want to track: whether you copy/paste it, or port
  it to another language, or even if you just use it as a reference, Raincoat just
  track the upstream code.
- Raincoat's builtin plugins don't run upstream code. That said, external pligins might
  do do.
- You probably shouldn't use raincoat as a linter on every pull request if you use
  updater plugins that fetch the latest version of the code, because it will
  likely fail on every PR if the upstream code has changed.
- For this reason, we have opted against providing a `.pre-commit-hooks.yaml` file.
  Also, it's probably to slow to run on every commit
- For the two reasons above, we recommend running Raincoat in CI, (or manually
  when you want to update your code.)

### v2?

Raincoat was created in 2016 and left dormant for a long time. It was revived in 2025,
redesigned and rewritten from the ground up, and given how (retrospectively) bad (IMHO)
some of _my_ initial design decisions were, it felt like completely breaking
compatibility with the previous version was a once-in-a-decade acceptable thing to do.

If you knew Raincoat before v2, congratulations, you're a long-time fan!

## Acknowledgments

This code is based on an idea we got at [Smart Impulse](http://smart-impulse.com)
around 2014. Kudos to them.
