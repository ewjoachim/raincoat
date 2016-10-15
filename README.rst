########
Raincoat
########

.. image:: https://badge.fury.io/py/raincoat.png
    :target: https://badge.fury.io/py/raincoat

.. image:: https://travis-ci.org/novafloss/raincoat.png?branch=master
    :target: https://travis-ci.org/novafloss/raincoat

.. image:: https://img.shields.io/codecov/c/github/novafloss/raincoat/master.svg
    :target: https://codecov.io/github/novafloss/raincoat?branch=master

.. image:: https://readthedocs.org/projects/raincoat/badge/?version=latest
    :target: http://raincoat.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

Raincoat has you covered when you can't stay DRY. When the time comes where you HAVE to copy code from a third party, Raincoat will let you know when this code is changed so that you can update your local copy.


The problem
===========

Lets say you're using a lib named ``umbrella`` which provides a function named ``use_umbrella`` and it reads as such :

.. code-block:: python

	def use_umbrella(umbrella):

		# Prepare umbrella
		umbrella.remove_pouch()
		umbrella.open()

		# Use umbrella
		while rain_detector.still_raining():
			umbrella.keep_over_me()

		# Put umbrella away
		umbrella.close()
		while not umbrella.is_wet():
			time.sleep(1)
		umbrella.put_pouch()

This function does what it says it does, but it's not ideally splitted, depending on your needs. For example, maybe at some point you realize you need each of the 3 separate parts to be a function of its own. Or maybe you can't call time.sleep in your app. Or do something else with the ``umbrella`` when it's open like dance with it.

It's also possible that you can't really make a pull request because your needs are specific, or you don't have the time (that's sad but, hey, I know it happens) or any other personnal reason. So what do you do ? There's no real alternative. You copy and paste the code, modify it to fit your needs and use your modified version. And whenever there's a change to the upstream function, chances are you'll never know.


The solution
============

Enter Raincoat.

You have made your own private copy of ``umbrella.use_umbrella`` (umbrella being at the time at version 14.5.7) and it looks like this :

.. code-block:: python

	def dance_with_umbrella(umbrella):
		"""
		I'm siiiiiinging in the rain !
		"""
		# Prepare umbrella
		umbrella.remove_pouch()
		umbrella.open()

		# Use umbrella
		while rain_detector.still_raining():
			Dancer.sing_in_the_rain(umbrella)

		# Put umbrella away
		umbrella.close()
		while not umbrella.is_wet()
			time.sleep(1)
		umbrella.put_pouch()

Now simply add a comment somewhere (preferably juste after the docstring) that says something like:

.. code-block:: python

	def dance_with_umbrella(umbrella):
		"""
		I'm siiiiiinging in the rain !
		"""
		# This code was adapted from the original umbrella.use_umbrella function
		# (we just changed the part inside the middle while loop)
		# Raincoat: package "umbrella==14.5.7" path "umbrella/__init__.py" "use_umbrella"

		...

Now, if you run ``raincoat`` in your project (At this stage, I assumed you've installed it with ``pip install raincoat``)

.. code-block:: bash

	$ raincoat


It will:

- Grep the code for all `# Raincoat:` comments and for each comment:
- Look at the currently installed version of the lib (say, umbrella 16.0.3) (or, if not found, the latest version)
- Compare with the version in the Raincoat comment (here, 14.5.7)
- If they are different, download and pip install the specified version in a temp dir (using cached wheel as pip does by default, this should be quite fast in most cases)
- Locate the code using the provided path for both the downloaded and the currently installed versions
- Diff it
- Tell you if there's a difference (and mention the location of the original Raincoat comment)

Whether there is something to change or not, you've now verified your code with umbrella 16.0.3, so you can update manually the umbrella comment.

.. code-block:: python

	# Raincoat: package "umbrella==16.0.3" path "umbrella/__init__.py" "use_umbrella"

Raincoat can be used like a linter, you can integrate it in CI, make it a tox target...

Note that if you omit the last argument, Raincoat will analyze the whole module:

.. code-block:: python

	# Raincoat: package "umbrella==16.0.3" path "umbrella/__init__.py"

Caveats and Gotchas
===================

- The 2 elements you provide in path should be the location of the file when the package is installed (in most case, this should match the location of the file in the project repo) and the object defined in this file. This object can be a variable, a class, a function or a method.
- Your own customized (copied/pasted) version of the function will not be analyzed. In fact, you don't even have to place the Raincoat comment in the function that uses it.
- You may realize that raincoat works best if you can use some kind of pip cache.
- Raincoat does not run files (either your files or the package file). Package files are parsed and the AST is analyzed.
- If for any reason, several code objects are identically named in the file you analyze, there's no guarantee you'll get any specific one.


Todos
=====

Things I'd like to add at some point

- An option to update a comment automatically
- A way to say you want your customized function to be diffed too (in case it's a close copy and you want to keep track of what you've modified)
- A way to access the original function without the process of downloading the whole package and installing it for nothing. We just want a single file of it.
- A smart way to make raincoat not need a pip cache (a cache of its own, or something)
- Add expected "--exclude" command line option


Acknowledgments
===============

This code is open-sourced and maintained by me (Joachim Jablon) during both my free time and my time working at `PeopleDoc <http://people-doc.com>`_, based on an idea and a first implemention made at `Smart Impulse <http://smart-impulse.com>`_. Kudos to these 2 companies.
