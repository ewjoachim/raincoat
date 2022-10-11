from __future__ import absolute_import, annotations

import os
import subprocess
import sys
import tarfile
import zipfile
from distutils.version import StrictVersion

import requests

from raincoat import github_utils
from raincoat.constants import FILE_NOT_FOUND

if sys.version_info < (3, 10):
    import importlib_metadata
else:
    from importlib import metadata as importlib_metadata


def download_package(package, version, download_dir):
    full_package = "{}=={}".format(package, version)

    result = subprocess.run(
        ["pip", "download", "--no-deps", "-d", download_dir, full_package]
    )
    if result.returncode != 0:
        raise ValueError(
            "Error while fetching {} via pip: {}".format(
                full_package, result.stdout.decode("utf-8")
            )
        )


def open_in_wheel(wheel, pathes):
    with zipfile.ZipFile(wheel, "r") as zf:
        sources = {}
        for path in pathes:
            try:
                source = zf.open(path, "r").read().decode("UTF-8")
            except KeyError:
                source = FILE_NOT_FOUND
            sources[path] = source
        return sources


def open_in_tarball(tarball, pathes):
    sources = {}
    with tarfile.open(tarball, "r:gz") as tf:
        for path in pathes:
            top_level_dir = tf.next().name
            try:
                handler = tf.extractfile(os.path.join(top_level_dir, path))
                source = handler.read().decode("UTF-8")
            except KeyError:
                source = FILE_NOT_FOUND
            sources[path] = source
    return sources


def open_downloaded(download_path, pathes):
    (archive_name,) = os.listdir(download_path)

    archive_path = os.path.join(download_path, archive_name)
    ext = os.path.splitext(archive_name)[1]

    if ext == ".gz":
        return open_in_tarball(archive_path, pathes)
    elif ext == ".whl":
        return open_in_wheel(archive_path, pathes)
    else:
        raise NotImplementedError("Unrecognize archive format {}".format(ext))


def open_installed(all_files, files_to_open):
    sources = {}
    for file in files_to_open:
        try:
            dist_file = all_files[file]
        except KeyError:
            source = FILE_NOT_FOUND
        else:
            source = dist_file.read_text()

        sources[file] = source

    return sources


def get_current_or_latest_version(package):
    try:
        return True, importlib_metadata.version(package)
    except importlib_metadata.PackageNotFoundError:
        pass
    pypi_url = "https://pypi.python.org/pypi/{}/json".format(package)
    response = requests.get(pypi_url)
    response.raise_for_status()
    releases = response.json()["releases"]

    versions = []

    for version in releases:
        try:
            parsed_version = StrictVersion(version)
        except ValueError:
            continue

        if parsed_version.prerelease:
            continue

        versions.append((parsed_version, version))

    return False, next(iter(sorted(versions, reverse=True)))[1]


def get_distributed_files(package):
    return {str(f): f for f in importlib_metadata.files(package) or []}


def get_branch_commit(repo, branch):
    # This may fail, but so far, I don't really know how.
    url = "https://api.github.com/repos/{}/branches/{}".format(repo, branch)
    with github_utils.get_session() as session:
        response = session.get(url)
        response.raise_for_status()
        return response.json()["commit"]["sha"]


def download_files_from_repo(repo, commit, files):
    result = {}

    template = "https://raw.githubusercontent.com/{}/{}/{}"
    with github_utils.get_session() as session:
        for filename in files:
            url = template.format(repo, commit, filename)
            response = session.get(url)
            if response.status_code != 200:
                content = FILE_NOT_FOUND
            else:
                content = response.text

            result[filename] = content

    return result
