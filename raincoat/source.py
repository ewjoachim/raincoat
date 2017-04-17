from __future__ import absolute_import

import os
import tarfile
import zipfile

from distutils.version import StrictVersion
import pip
import pkg_resources
import requests

from raincoat.constants import FILE_NOT_FOUND


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
