"""Source plugins for fetching code from different sources."""

from __future__ import annotations

import base64
import io
import os
import pathlib
import tarfile
from typing import Any

import httpx
from packaging.utils import canonicalize_name

from raincoat import exceptions
from raincoat.plugins.wheel_reader import read_file_from_wheel


async def pypi(
    *,
    version: str,
    package: str,
    path: str,
    use_sdist: bool = False,
    match_wheel: str = "*",
) -> str:
    """
    A source plugin that fetches code from PyPI packages. Uses wheels (default) or
    source distributions.

    Parameters
    ----------
    version:
        The version of the package to fetch
    package:
        The name of the package on PyPI
    path:
        Path to the file within the package (e.g., 'mypackage/module.py')
    use_sdist:
        If True, fetch the source distribution instead of a wheel
    match_wheel:
        Optional glob pattern to match wheel filenames (default is '*'). The first
        matching wheel will be used. (e.g., '*x86_64*')

    Returns
    -------
    str
        The source code from the specified location
    """
    # Get package download URL from PyPI
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://pypi.org/pypi/{package}/{version}/json")
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise exceptions.PypiPackageNotFoundError(
                package=package, version=version
            ) from exc
        api_data = response.json()

    if use_sdist:
        return await fetch_sdist(
            package=package,
            version=version,
            path=path,
            api_data=api_data,
        )
    else:
        return await fetch_wheel(
            package=package,
            version=version,
            path=path,
            match_wheel=match_wheel,
            api_data=api_data,
        )


async def fetch_wheel(
    *,
    package: str,
    version: str,
    path: str,
    match_wheel: str,
    api_data: dict[str, Any],
) -> str:
    wheel_url = find_wheel_url(
        package=package, version=version, match_wheel=match_wheel, api_data=api_data
    )

    # First try with normalized package name (PEP 503)
    normalized_path = f"{canonicalize_name(package)}/{path}"

    try:
        return await read_file_from_wheel(url=wheel_url, path=normalized_path)
    except KeyError as exc:
        raise exceptions.PypiFileNotFoundError(
            package=package, version=version, path=path
        ) from exc


def find_wheel_url(
    *,
    package: str,
    version: str,
    match_wheel: str,
    api_data: dict[str, Any],
):
    for url in api_data["urls"]:
        is_wheel = url["packagetype"] == "bdist_wheel"
        matches = pathlib.Path(url["filename"]).match(match_wheel)

        if is_wheel and matches:
            return url["url"]

    raise exceptions.PypiWheelDistributionNotFoundError(
        package=package, version=version, match=match_wheel
    )


async def fetch_sdist(
    *,
    package: str,
    version: str,
    path: str,
    api_data: dict[str, Any],
) -> str:
    """
    Fetch a file from a source distribution.

    This downloads and extracts the entire sdist since they can use various
    compression formats and don't support random access like wheels do.
    """
    # Find source distribution
    sdist_url = None
    for url in api_data["urls"]:
        if url["packagetype"] == "sdist":
            sdist_url = url["url"]
            break
    else:
        raise exceptions.PypiSdistDistributionNotFoundError(
            package=package,
            version=version,
        )

    # Download and extract the source
    async with httpx.AsyncClient() as client:
        response = await client.get(sdist_url)
        response.raise_for_status()

        # Extract source
        with tarfile.open(fileobj=io.BytesIO(response.content)) as tar:
            pkg_dir = pathlib.PurePath(f"{package}-{version}")
            member = pkg_dir / path

            try:
                info = tar.getmember(str(member))
            except KeyError:
                raise exceptions.PypiFileNotFoundError(
                    package=package,
                    version=version,
                    path=path,
                )

            extracted = tar.extractfile(info)
            if not extracted:
                raise exceptions.PypiFileNotFoundError(
                    package=package,
                    version=version,
                    path=path,
                )
            return extracted.read().decode("utf-8")


async def github(
    *,
    version: str,
    repo: str,
    path: str,
    **config: Any,
) -> str:
    """
    A source plugin that fetches code from GitHub repositories.

    Parameters
    ----------
    version:
        The commit hash, tag, or branch to fetch from
    repo:
        The GitHub repository in owner/repo format
    path:
        Path to the file within the repository
    **config:
        Additional configuration options:
        - element: Optional element (function/class) within the file to extract

    Returns
    -------
    str
        The source code from the specified location
    """
    headers = {}
    if "GITHUB_TOKEN" in os.environ:
        headers["Authorization"] = f"token {os.environ['GITHUB_TOKEN']}"

    async with httpx.AsyncClient(headers=headers) as client:
        # Get the file content
        response = await client.get(
            f"https://api.github.com/repos/{repo}/contents/{path}",
            # If we don't pass this header, the format of the answer will depend on
            # the size of the file. With the header, we're sure to get the raw content.
            headers={"Accept": "application/vnd.github.raw+json"},
            params={"ref": version},
        )
        response.raise_for_status()
        data = response.json()

        if "content" not in data:
            raise ValueError(f"Could not fetch {path} from {repo} at {version}")

        content = base64.b64decode(data["content"]).decode("utf-8")
        return content
