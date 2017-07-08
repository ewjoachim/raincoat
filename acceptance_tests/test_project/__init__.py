"""
Raincoat comments that are checked in acceptance tests
"""


def simple_function():
    # Raincoat: pypi package: raincoat==0.1.4 path: raincoat/_acceptance_test.py element: use_umbrella  # noqa
    # Raincoat: pypi package: raincoat==0.1.4 path: raincoat/_acceptance_test.py element: Umbrella.open  # noqa
    # Raincoat: pypi package: raincoat==0.1.4 path: raincoat/_acceptance_test.py element: Umbrella  # noqa
    # Raincoat: pypi package: raincoat==0.1.4 path: raincoat/_acceptance_test.py # noqa
    # Raincoat: pypi package: raincoat==0.1.4 path: raincoat/_acceptance_test.py element: non_existant # noqa
    # Raincoat: pypi package: raincoat==0.1.4 path: raincoat/non_existant.py # noqa
    # Raincoat: django ticket: #25981
    # Raincoat: django ticket: #27754
    # Raincoat: pygithub repo: novafloss/raincoat@a35df1d path: raincoat/_acceptance_test.py element: Umbrella.open  # noqa
    pass


# this file should never be executed, only parsed.
raise NotImplementedError
