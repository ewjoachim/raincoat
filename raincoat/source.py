from __future__ import absolute_import

import os
import tarfile
import zipfile

from distutils.version import StrictVersion
import pip
import pkg_resources
import requests

from raincoat.constants import FILE_NOT_FOUND
from raincoat import github_utils


def download_package(package, version, download_dir):
    full_package = "{}=={}".format(package, version)

    exit_code = pip.main(
        ["download", "--no-deps", "-d", download_dir, full_package])
    if exit_code != 0:
        raise ValueError("Error while fetching {} via pip.".format(
            full_package))


def open_in_wheel(wheel, pathes):
    with zipfile.ZipFile(wheel, 'r') as zf:
        sources = {}
        for path in pathes:
            try:
                source = zf.open(path, 'r').read().decode("UTF-8")
            except KeyError:
                source = FILE_NOT_FOUND
            sources[path] = source
        return sources


def open_in_tarball(tarball, pathes):
    sources = {}
    with tarfile.open(tarball, 'r:gz') as tf:
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
    archive_name, = os.listdir(download_path)

    archive_path = os.path.join(download_path, archive_name)
    ext = os.path.splitext(archive_name)[1]

    if ext == ".gz":
        return open_in_tarball(archive_path, pathes)
    elif ext == ".whl":
        return open_in_wheel(archive_path, pathes)
    else:
        raise NotImplementedError("Unrecognize archive format {}".format(ext))


def open_installed(installed_path, pathes):
    sources = {}
    for path in pathes:
        try:
            source = open(os.path.join(installed_path, path)).read()
        except IOError:
            source = FILE_NOT_FOUND
        sources[path] = source

    return sources


def get_current_or_latest_version(package):
    try:
        return True, pkg_resources.get_distribution(package).version
    except pkg_resources.DistributionNotFound:
        pass
    pypi_url = "http://pypi.python.org/pypi/{}/json".format(package)
    releases = requests.get(pypi_url).json()["releases"]

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


def get_current_path(package):
    return pkg_resources.get_distribution(package).location


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
        for file in files:
            url = template.format(repo, commit, file)
            response = session.get(url)
            if response.status_code != 200:
                content = FILE_NOT_FOUND
            else:
                content = response.text

            result[file] = content

    return result
