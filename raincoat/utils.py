import os
import shutil
import tempfile


class Cleaner(object):
    """
    Context manager that takes care of deleting
    objects when it goes out of scope.
    """
    def __init__(self):
        self.elements = set()

    def __enter__(self):
        return self

    def add(self, path):
        self.elements.add(path)
        return path

    def mkdir(self):
        return self.add(tempfile.mkdtemp())

    def __exit__(self, *args, **kwargs):
        for element in self.elements:
            if os.path.exists(element):
                if os.path.isdir(element):
                    shutil.rmtree(element)
                else:
                    os.remove(element)
