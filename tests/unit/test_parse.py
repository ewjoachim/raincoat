import os

from raincoat import constants
from raincoat import parse


umbrella_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), "umbrella"))

umbrella_file = os.path.join(umbrella_dir, "__init__.py")


def test_find_function():
    code_blocks = list(
        parse.find_elements(open(umbrella_file).read(), ["use_umbrella"])
    )

    assert len(code_blocks) == 1
    name, lines = code_blocks[0]

    print(lines)

    assert name == "use_umbrella"
    assert len(lines) == 15
    assert lines[0] == ("def use_umbrella(umbrella, action):")
    assert lines[-1] == ("    umbrella.put_pouch()")


def test_find_method():
    code_blocks = list(
        parse.find_elements(open(umbrella_file).read(), ["Umbrella.open"])
    )

    assert len(code_blocks) == 1
    name, lines = code_blocks[0]

    print(lines)
    assert name == "Umbrella.open"
    assert len(lines) == 9
    assert lines[0] == ("    def open(self):")
    assert lines[-1] == ('        self.side = "pointy side up"')


def test_find_class():
    code_blocks = list(parse.find_elements(open(umbrella_file).read(), ["Umbrella"]))

    assert len(code_blocks) == 1
    name, lines = code_blocks[0]

    print(lines)
    assert name == "Umbrella"
    assert len(lines) == 27
    assert lines[0] == ("class Umbrella(object):")
    assert lines[-1] == ("        return True")


def test_find_module():
    code_blocks = list(parse.find_elements(open(umbrella_file).read(), [""]))

    assert len(code_blocks) == 1
    name, lines = code_blocks[0]

    print(lines)
    assert name == ""
    assert len(lines) == 92
    assert lines[0] == ('"""')
    assert lines[-1] == ("    pass")


def test_find_several():
    code_blocks = list(
        parse.find_elements(
            open(umbrella_file).read(), ["use_umbrella", "Umbrella.open", ""]
        )
    )

    assert len(code_blocks) == 3


def test_outer_inner():
    code_blocks = dict(
        parse.find_elements(open(umbrella_file).read(), ["outer", "outer.inner"])
    )

    assert len(code_blocks) == 2

    assert len(code_blocks["outer"]) == 4

    assert len(code_blocks["outer.inner"]) == 2


def test_one_liner():
    one_liner_file = os.path.join(umbrella_dir, "oneliner.py")

    code_blocks = list(parse.find_elements(open(one_liner_file).read(), ["a"]))

    assert len(code_blocks) == 1
    name, lines = code_blocks[0]

    print(lines)
    assert name == "a"
    assert len(lines) == 1
    assert lines == ["def a(): pass  # noqa"]


def test_find_function_not_found():
    code_blocks = list(parse.find_elements(" ", ["a"]))

    assert code_blocks == [("a", constants.ELEMENT_NOT_FOUND)]


def test_empty_file():
    list(parse.find_elements("", ["a"]))
