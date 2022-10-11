from __future__ import annotations

import os

import requests


def get_session():
    session = requests.Session()
    token = os.getenv("RAINCOAT_GITHUB_TOKEN")
    if token:
        session.auth = tuple(token.split(":"))
    return session
