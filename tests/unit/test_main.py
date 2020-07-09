import pytest

from raincoat import __main__


@pytest.mark.parametrize("name, called", [("something", False), ("__main__", True)])
def test_main(mocker, name, called):
    cli = mocker.patch("raincoat.cli.cli")
    __main__.main(name)
    assert cli.called is called
