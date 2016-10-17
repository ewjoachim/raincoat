import os

from raincoat.utils import Cleaner


def test_cleaner_file(tmpdir):
    garbage_dir = tmpdir.mkdir("garbage_dir")

    with Cleaner() as cleaner:
        filename = garbage_dir.join("bla.txt")
        filename.write("yay")
        assert os.path.exists(filename.strpath)
        cleaner.add(filename.strpath)

    assert not os.path.exists(filename.strpath)


def test_cleaner_folder(tmpdir):
    garbage_dir = tmpdir.mkdir("garbage_dir")

    with Cleaner() as cleaner:
        filename = garbage_dir.join("bla")
        filename.mkdir()
        assert os.path.exists(filename.strpath)
        cleaner.add(filename.strpath)

    assert not os.path.exists(filename.strpath)


def test_cleaner_add_folder():

    with Cleaner() as cleaner:
        dir_name = cleaner.mkdir()
        assert os.path.exists(dir_name)

    assert not os.path.exists(dir_name)
