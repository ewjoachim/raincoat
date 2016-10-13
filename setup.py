#!/usr/bin/env python
# -*- coding: utf-8 -*-
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

version = '0.1.5'

readme = open('README.rst').read()
history = open('HISTORY.rst').read().replace('.. :changelog:', '')

setup(
    name='raincoat',
    version=version,
    description="Raincoat has your code covered when you can't stay DRY.",
    long_description=readme + '\n\n' + history,
    author='Joachim Jablon',
    author_email='joachim.jablon@people-doc.com',
    url='https://github.com/novafloss/raincoat',
    packages=[
        'raincoat',
    ],
    include_package_data=True,
    install_requires=["sh", "requests", "pip"],
    tests_require=["tox"],
    license="MIT",
    zip_safe=False,
    entry_points={
        'console_scripts': ['raincoat=raincoat:main'],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
)
