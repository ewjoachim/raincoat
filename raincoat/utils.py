from __future__ import annotations

import logging
import os
import shutil
import tempfile

logger = logging.getLogger(__name__)


def causes(exc: BaseException | None):
    """
    From a single exception with a chain of causes and contexts, make an iterable
    going through every exception in the chain.
    """
    while exc:
        yield exc
        exc = exc.__cause__ or exc.__context__


class Cleaner(object):
    """
    Context manager that takes care of deleting
    file when it goes out of scope.
    """

    def __init__(self):
        self.files = set()
        self.dirs = set()

    def __enter__(self):
        return self

    def add(self, path):
        if os.path.isdir(path):
            self.dirs.add(path)
        else:
            self.files.add(path)
        return path

    def mkdir(self):
        path = tempfile.mkdtemp()
        self.dirs.add(path)
        return path

    def __exit__(self, *args, **kwargs):
        for element in self.files:
            if os.path.exists(element):
                os.remove(element)

        for element in self.dirs:
            shutil.rmtree(element)
