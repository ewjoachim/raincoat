"""Updater plugins for determining current versions."""

from __future__ import annotations

import importlib.metadata
import os
from typing import Any

import httpx


async def venv(*, package: str, **config: Any) -> str:
    """
    An updater plugin that checks the installed version in the current virtualenv.

    Parameters
    ----------
    package:
        The name of the package to check
    **config:
        Additional configuration options

    Returns
    -------
    str
        The installed version of the package
    """
    try:
        return importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        raise ValueError(f"Package {package} not found in current environment")


async def github_tag(*, repo: str, remove_v_prefix: bool = True, **config: Any) -> str:
    """
    An updater plugin that gets the latest tag from GitHub.

    Parameters
    ----------
    repo:
        The GitHub repository in owner/repo format
    latest_tag:
        If True, return the latest tag (default False)

    remove_v_prefix:
        If True (default) and using tags, remove 'v' prefix from version numbers
    **config:
        (unused)

    Returns
    -------
    str
        The latest tag
    """
    headers = {}
    if "GITHUB_TOKEN" in os.environ:
        headers["Authorization"] = f"token {os.environ['GITHUB_TOKEN']}"

    async with httpx.AsyncClient(headers=headers) as client:
        # Get latest tag
        response = await client.get(f"https://api.github.com/repos/{repo}/tags")
        response.raise_for_status()
        tags = response.json()
        if not tags:
            raise ValueError(f"No tags found in repository {repo}")
        version = tags[0]["name"]
        if remove_v_prefix and version.startswith("v"):
            version = version.removeprefix("v")
        return version


async def github_branch(
    *,
    repo: str,
    branch: str | None = None,
    **config: Any,
) -> str:
    """
    An updater plugin that gets the head commit of a branch from GitHub.
    Defaults to the default branch.

    Parameters
    ----------
    repo:
        The GitHub repository in owner/repo format
    branch:
        The branch name to check (default: None, which uses the default branch)
    **config:
        (unused)

    Returns
    -------
    str
        The commit hash of the head on the branch
    """
    headers = {}
    if "GITHUB_TOKEN" in os.environ:
        headers["Authorization"] = f"token {os.environ['GITHUB_TOKEN']}"

    async with httpx.AsyncClient(headers=headers) as client:
        if not branch:
            # Get default branch
            response = await client.get(f"https://api.github.com/repos/{repo}")
            response.raise_for_status()
            branch = response.json()["default_branch"]

        # Get latest commit on branch
        response = await client.get(
            f"https://api.github.com/repos/{repo}/commits/{branch}"
        )
        response.raise_for_status()
        commit = response.json()
        return commit["sha"]
