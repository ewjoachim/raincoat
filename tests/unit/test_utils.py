from __future__ import annotations

import os

from raincoat import utils


def test_causes():
    e1, e2, e3 = AttributeError("foo"), KeyError("bar"), IndexError("baz")

    try:
        try:
            # e3 will be e2's __cause__
            raise e2 from e3
        except Exception:
            # e2 will be e1's __context__
            raise e1
    except Exception as exc2:
        result = list(utils.causes(exc2))

    assert result == [e1, e2, e3]


def test_cleaner_file(tmpdir):
    garbage_dir = tmpdir.mkdir("garbage_dir")

    with utils.Cleaner() as cleaner:
        filename = garbage_dir.join("bla.txt")
        filename.write("yay")
        assert os.path.exists(filename.strpath)
        cleaner.add(filename.strpath)

    assert not os.path.exists(filename.strpath)


def test_cleaner_folder(tmpdir):
    garbage_dir = tmpdir.mkdir("garbage_dir")

    with utils.Cleaner() as cleaner:
        filename = garbage_dir.join("bla")
        filename.mkdir()
        assert os.path.exists(filename.strpath)
        cleaner.add(filename.strpath)

    assert not os.path.exists(filename.strpath)


def test_cleaner_add_folder():
    with utils.Cleaner() as cleaner:
        dir_name = cleaner.mkdir()
        assert os.path.exists(dir_name)

    assert not os.path.exists(dir_name)


def test_cleaner_missing_file(tmpdir):
    with utils.Cleaner() as cleaner:
        cleaner.add("/tmp/bla/yay")
