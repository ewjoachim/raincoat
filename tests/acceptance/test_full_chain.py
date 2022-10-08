import subprocess


def test_full_chain():
    """
    Note that this test is excluded from coverage because coverage should be
    for unit tests.
    """

    result = subprocess.run(
        ["raincoat", "tests/acceptance/test_project", "--exclude=*ignored*"],
        stdout=subprocess.PIPE,
    )
    output = result.stdout.decode("utf-8")
    print(output)
    assert result.returncode != 0

    details = (
        f"raincoat == 0.1.4 vs 0.0.0 "
        "@ raincoat/_acceptance_test.py:use_umbrella "
        "(from tests/acceptance/test_project/__init__.py:7)"
    )

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

    assert "peopledoc/raincoat@a35df1d vs master branch" in output

    assert "non_existant does not exist in raincoat/_acceptance_test.py" in output

    assert "raincoat/non_existant.py does not exist" in output
