from raincoat import exceptions


def test_base_exception():
    class TestException(exceptions.RaincoatException):
        """Foo"""

    assert str(TestException) == "Foo"
