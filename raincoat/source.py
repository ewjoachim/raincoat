import os
import tarfile
import zipfile

import pip


def download_package(package, download_dir, version=None):
    if version:
        package = "{}=={}".format(package, version)

    pip.main(["download", "--no-deps", "-d", download_dir, package])


def open_in_wheel(wheel, path):
    with zipfile.ZipFile(wheel, 'r') as zf:
        return zf.open(path, 'r').read().decode("UTF-8")


def open_in_tarball(tarball, path):
    with tarfile.open(tarball, 'r:gz') as tf:
        top_level_dir = tf.next().name
        handler = tf.extractfile(os.path.join(top_level_dir, path))
        return handler.read().decode("UTF-8")


def open_downloaded(download_path, path):
    archive_name, = os.listdir(download_path)

    archive_path = os.path.join(download_path, archive_name)
    ext = os.path.splitext(archive_name)[1]

    if ext == ".gz":
        return open_in_tarball(archive_path, path)
    elif ext == ".whl":
        return open_in_wheel(archive_path, path)
    else:
        raise NotImplementedError("Unrecognize archive format {}".format(ext))
