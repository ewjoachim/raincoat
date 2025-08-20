from __future__ import annotations

import pydantic
import pytest

from raincoat.settings import models


def test_len_1():
    assert models.len_1({"foo": "bar"}) == {"foo": "bar"}


@pytest.mark.parametrize(
    "input",
    [
        {},
        {"foo": 1, "bar": 2},
    ],
)
def test_len_1__error(input):
    with pytest.raises(ValueError):
        models.len_1(input)


def test_config_check():
    models.ConfigCheck.model_validate(
        {
            "version": "1.2.3",
            "location": "foo",
            "source": {"pypi": {"package": "bar", "path": "baz"}},
            "diff": {"python": {"element": "qux"}},
            "updater": {"venv": {}},
        }
    )


def test_config_check__minimal():
    models.ConfigCheck.model_validate(
        {
            "version": "1.2.3",
            "location": "foo",
            "source": {"pypi": {"package": "bar", "path": "baz"}},
        }
    )


def test_config_check__error():
    with pytest.raises(pydantic.ValidationError):
        models.ConfigCheck.model_validate(
            {
                "version": "1.2.3",
                "location": "foo",
                "source": {"pypi": {"package": "bar", "path": "baz", "unexpected": ""}},
            }
        )
