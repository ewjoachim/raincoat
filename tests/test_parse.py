import os

from raincoat import parse


umbrella_file = os.path.normpath(os.path.join(os.path.dirname(__file__),
                                              "package/umbrella",
                                              "__init__.py"))


def test_find_function():
    code_blocks = list(parse.find_objects(
        open(umbrella_file).read(), ["use_umbrella"]))

    assert len(code_blocks) == 1

    for name, lines in code_blocks:
        assert name == "use_umbrella"
        assert len(lines) == 15
        assert lines[0] == ('def use_umbrella(umbrella, action):')
        assert lines[-1] == ('    umbrella.put_pouch()')


def test_find_method():
    code_blocks = list(parse.find_objects(
        open(umbrella_file).read(), ["Umbrella.open"]))

    assert len(code_blocks) == 1

    for name, lines in code_blocks:
        assert name == "Umbrella.open"
        assert len(lines) == 9
        assert lines[0] == ('    def open(self):')
        assert lines[-1] == ('        self.side = "pointy side up"')


def test_find_class():
    code_blocks = list(parse.find_objects(
        open(umbrella_file).read(), ["Umbrella"]))

    assert len(code_blocks) == 1

    for name, lines in code_blocks:
        assert name == "Umbrella"
        assert len(lines) == 27
        assert lines[0] == ('class Umbrella(object):')
        assert lines[-1] == ('        return True')


def test_find_module():
    code_blocks = list(parse.find_objects(
        open(umbrella_file).read(), [None]))

    assert len(code_blocks) == 1

    for name, lines in code_blocks:
        assert name is None
        assert len(lines) == 85
        assert lines[0] == ('"""')
        assert lines[-1] == ('    return string')


def test_find_several():
    code_blocks = list(parse.find_objects(
        open(umbrella_file).read(), ["use_umbrella", "Umbrella.open", None]))

    assert len(code_blocks) == 3
