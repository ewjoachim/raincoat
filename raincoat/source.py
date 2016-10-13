from __future__ import absolute_import

import os
import tarfile
import zipfile

import pip
import pkg_resources
import requests


def download_package(package, version, download_dir):
    full_package = "{}=={}".format(package, version)

    exit_code = pip.main(
        ["download", "--no-deps", "-d", download_dir, full_package])
    if exit_code != 0:
        raise ValueError("Error while fetching {} via pip.".format(
            full_package))


def open_in_wheel(wheel, pathes, package):
    with zipfile.ZipFile(wheel, 'r') as zf:
        return {
            path: zf.open(path, 'r').read().decode("UTF-8")
            for path in pathes
        }


def open_in_tarball(tarball, pathes, package):
    result = {}
    with tarfile.open(tarball, 'r:gz') as tf:
        for path in pathes:
            top_level_dir = tf.next().name
            try:
                handler = tf.extractfile(os.path.join(top_level_dir, path))
            except KeyError:
                raise ValueError("File {} does not exist in package {}".format(
                    path, package))
            result[path] = handler.read().decode("UTF-8")
    return result


def open_downloaded(download_path, pathes, package):
    archive_name, = os.listdir(download_path)

    archive_path = os.path.join(download_path, archive_name)
    ext = os.path.splitext(archive_name)[1]

    if ext == ".gz":
        return open_in_tarball(archive_path, pathes, package)
    elif ext == ".whl":
        return open_in_wheel(archive_path, pathes, package)
    else:
        raise NotImplementedError("Unrecognize archive format {}".format(ext))


def open_installed(installed_path, pathes):
    return {
        path: open(os.path.join(installed_path, path)).read()
        for path in pathes
    }


def get_current_or_latest_version(package):
    try:
        return True, pkg_resources.get_distribution(package).version
    except pkg_resources.DistributionNotFound:
        pypi_url = "http://pypi.python.org/pypi/{}/json".format(package)
        return False, requests.get(pypi_url).json()["info"]["version"]


def get_current_path(package):
    return pkg_resources.get_distribution(package).location
