from raincoat import exceptions


def test_raincoat_exception():
    class TestException(exceptions.RaincoatException):
        """Foo"""

    assert str(TestException()) == "Foo"
