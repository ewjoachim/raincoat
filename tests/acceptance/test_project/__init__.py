"""
Raincoat comments that are checked in acceptance tests
"""


def simple_function():
    # Raincoat: pypi package: raincoat_umbrella==1.0.0 path: umbrella/__init__.py element: main
    # Raincoat: pypi package: raincoat_umbrella==1.0.0 path: umbrella/__init__.py element: Drop.fall
    # Raincoat: pypi package: raincoat_umbrella==1.0.0 path: umbrella/__init__.py element: Drop
    # Raincoat: pypi package: raincoat_umbrella==1.0.0 path: umbrella/__init__.py
    # Raincoat: pypi package: raincoat_umbrella==1.0.0 path: umbrella/__init__.py element: non_existant
    # Raincoat: pypi package: raincoat_umbrella==1.0.0 path: umbrella/non_existant.py
    # Raincoat: django ticket: #25981
    # Raincoat: django ticket: #27754
    # Raincoat: pygithub repo: ewjoachim/umbrella@1.0.0 path: umbrella/__init__.py element: main
    pass


# this file should never be executed, only parsed.
raise NotImplementedError
