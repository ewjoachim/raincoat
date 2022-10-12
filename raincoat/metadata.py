from __future__ import annotations

import sys
from typing import Mapping

if sys.version_info < (3, 10):
    import importlib_metadata
else:
    from importlib import metadata as importlib_metadata


def extract_metadata() -> Mapping[str, str]:

    # Backport of Python 3.8's future importlib.metadata()
    metadata = importlib_metadata.metadata("raincoat")

    return {
        "author": metadata["Author"],
        "email": metadata["Author-email"],
        "license": metadata["License"],
        "url": metadata["Home-page"],
        "version": metadata["Version"],
    }
