import pytest
import traceback

from raincoat import main
from raincoat import __version__


def test_full_chain(cli_runner):
    """
    Note that this test is excluded from coverage because coverage should be
    for unit tests.
    """
    result = cli_runner.invoke(main, ["--path=acceptance_tests/test_project"])

    if result.exception and not isinstance(result.exception, SystemExit):
        traceback.print_exception(*result.exc_info)
        pytest.fail()

    details = ("raincoat == 0.1.4 vs {} "
               "@ raincoat/_acceptance_test.py:use_umbrella "
               "(from acceptance_tests/test_project/__init__.py:2)").format(
                    __version__)

    print(result.output, )

    assert details in result.output
    assert "_acceptance_test.py:Umbrella.open" in result.output
    # space left intentionally at the end to not match the previous line
    assert "_acceptance_test.py:Umbrella " in result.output
    assert "_acceptance_test.py:whole module" in result.output

    assert "-        umbrella.keep_over_me()" in result.output
    assert "+        action(umbrella)" in result.output

    assert "27754" not in result.output
    assert "Ticket #25981 has been merged in Django" in result.output
