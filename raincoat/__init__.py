"""
Raincoat has you covered when you code is not dry.

Project homepage is https://github.com/peopledoc/raincoat/

Documentation available at
http://raincoat.readthedocs.io/en/stable/?badge=latest

Done with :heart: by Joachim "ewjoachim" Jablon, with support
from Smart Impulse and PeopleDoc

Thank you for using this package !

MIT License - Copyright (c) 2016, Joachim Jablon
Full license text available at
https://github.com/peopledoc/raincoat/blob/master/LICENSE

up up down down left right left right b a
"""

from __future__ import annotations

from raincoat import metadata as _metadata_module
from raincoat.match import Checker, Match, NotMatching

__all__ = ["Match", "Checker", "NotMatching"]


_metadata = _metadata_module.extract_metadata()
__author__ = _metadata["author"]
__author_email__ = _metadata["email"]
__license__ = _metadata["license"]
__url__ = _metadata["url"]
__version__ = _metadata["version"]
