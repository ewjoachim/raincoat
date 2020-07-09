from raincoat.color import COLOR_DICT, Color, get_color


def test_get_color_no_color():
    assert get_color(False).color_dict == {}


def test_get_color_color():
    assert get_color(True).color_dict == COLOR_DICT


def test_color_get():
    assert Color({"a": "b"}).get("a") == "b"


def test_color_get_absent():
    assert Color({"a": "b"}).get("c") == ""


def test_color_getitem():
    text = Color({"a": "b", "neutral": "n"})["a"]("c")
    assert text == "b" "c" "n"


def test_color_getitem_absent():
    assert Color({})["a"]("c") == "c"
