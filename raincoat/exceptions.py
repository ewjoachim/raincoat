from __future__ import annotations


class RaincoatError(Exception):
    """There was an error in the raincoat library."""

    def __init__(self, message: str = "", **kwargs) -> None:
        message = message or type(self).__doc__ or ""
        message = message.format(**kwargs)

        super().__init__(message)


class RaincoatConfigFormatError(RaincoatError):
    """The configuration file is not in the expected format: {error}"""


class PythonDiffSyntaxError(exceptions.RaincoatError):
    """Syntax error when parsing Python file to compare code: {error}"""


class PythonDiffElementNotFoundError(exceptions.RaincoatError):
    """Element {element} not found in Python source code"""


class PypiPackageNotFoundError(RaincoatError):
    """Package {package}=={version} not found in PyPI repository"""


class PypiWheelDistributionNotFoundError(RaincoatError):
    """Wheel distribution matching {match} for {package}=={version} not found in PyPI repository"""


class PypiSdistDistributionNotFoundError(RaincoatError):
    """Source distribution for {package}=={version} not found in PyPI repository"""


class PypiFileNotFoundError(RaincoatError):
    """File {path} not found in package {package}=={version}"""
