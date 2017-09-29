import traceback

import sh

from raincoat import __version__


def main():
    """
    Note that this test is excluded from coverage because coverage should be
    for unit tests.
    """

    result = sh.raincoat(
        "acceptance_tests/test_project", exclude="*ignored*",
        _ok_code=1)

    output = result.stdout.decode("utf-8")
    try:
        check_output(output)
    except AssertionError:
        print("Full output:\n", output)
        raise

    print("Ok")


def check_output(output):
    details = ("raincoat == 0.1.4 vs {} "
               "@ raincoat/_acceptance_test.py:use_umbrella "
               "(from acceptance_tests/test_project/__init__.py:7)").format(
                    __version__)

    assert details in output
    assert "_acceptance_test.py:Umbrella.open" in output
    # space left intentionally at the end to not match the previous line
    assert "_acceptance_test.py:Umbrella " in output
    assert "_acceptance_test.py:whole module" in output

    assert "-        umbrella.keep_over_me()" in output
    assert "+        action(umbrella)" in output

    assert "ignored" not in output

    assert "27754" not in output
    assert "Ticket #25981 has been merged in Django" in output

    assert "novafloss/raincoat@a35df1d vs master branch" in output

    assert ("non_existant does not exist in raincoat/_acceptance_test.py"
            in output)

    assert "raincoat/non_existant.py does not exist" in output


if __name__ == '__main__':
    main()
