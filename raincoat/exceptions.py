from __future__ import annotations


class RaincoatError(Exception):
    """There was an error in the raincoat library."""

    def __init__(self, message: str = "", **kwargs) -> None:
        message = message or type(self).__doc__ or ""
        message = message.format(**kwargs)

        super().__init__(message)


class ConfigFormatError(RaincoatError):
    """The configuration file is not in the expected format: {error}"""


class InlineConfigFormatError(RaincoatError):
    """Invalid inline comment format in {path}:{line}: {error}"""


class PythonDiffSyntaxError(RaincoatError):
    """Syntax error when parsing Python file to compare code: {error}"""


class PythonDiffElementNotFoundError(RaincoatError):
    """Element "{element}" not found in Python source code"""


class PypiPackageNotFoundError(RaincoatError):
    """Package "{package}=={version}" not found in PyPI repository"""


class PypiWheelDistributionNotFoundError(RaincoatError):
    """Wheel distribution matching "{match}" for "{package}=={version}" not found in PyPI repository"""


class PypiSdistDistributionNotFoundError(RaincoatError):
    """Source distribution for "{package}=={version}" not found in PyPI repository"""


class PypiFileNotFoundError(RaincoatError):
    """File {path} not found in package "{package}=={version}" """


class TomlParseError(RaincoatError):
    """Error parsing TOML file: {error}"""


# When the duplicate is with a raincoat config file
class DuplicateCommentError(RaincoatError):
    """Duplicate inline comment for check "{name}" in {path}:{line} and {other_path}"""


class PluginNotFound(RaincoatError):
    """{type} plugin with name "{name}" not found"""


class PluginNotACoroutine(RaincoatError):
    """{type} plugin "{name}" is not a coroutine"""


class InvalidPluginConfiguration(RaincoatError):
    """Invalid configuration for {type} plugin "{name}": {error}"""


class ConfigNotFound(RaincoatError):
    """Cannot find inline comments: {names}"""


class ConfigNotFoundInPath(ConfigNotFound):
    """Cannot find inline comment {name} in {path}"""


class InconsistentState(RaincoatError):
    """In check "{name}": new_version cannot be unset if old_version is set."""
