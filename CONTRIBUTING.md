## Development

This project uses [uv](https://docs.astral.sh/uv/).

If you don't have uv installed, install it with:

```console
$ curl -LsSf https://astral.sh/uv/install.sh | sh
```

or using a package manager, such as [brew](https://brew.sh/):

```console
$ brew install uv
```

Then you can directly launch the tests with:

```console
$ uv run pytest
```

or create a virtual environment to work on the package and activate it:

```console
$ uv sync
$ source .venv/bin/activate
```

or launch the command itself with uv (no need to activate the venv):

```console
$ uv run raincoat --help
```
