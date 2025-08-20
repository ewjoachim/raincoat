from __future__ import annotations

import pytest

from raincoat import __main__


@pytest.mark.parametrize(
    "name, result",
    [
        ("__main__", [True]),
        ("foo", []),
    ],
)
def test_main(name, result):
    called = []

    def run():
        called.append(True)

    __main__.main(name, run=run)

    assert called == result
