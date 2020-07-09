Raincoat
========

.. image:: https://badge.fury.io/py/raincoat.svg
    :target: https://pypi.org/pypi/raincoat
    :alt: Deployed to PyPI

.. image:: https://readthedocs.org/projects/raincoat/badge/?version=latest
    :target: http://raincoat.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://travis-ci.org/ewjoachim/raincoat.svg?branch=master
    :target: https://travis-ci.org/ewjoachim/raincoat
    :alt: Continuous Integration Status

.. image:: https://codecov.io/gh/ewjoachim/raincoat/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/ewjoachim/raincoat
    :alt: Coverage Status

.. image:: https://img.shields.io/badge/License-MIT-green.svg
    :target: https://github.com/ewjoachim/raincoat/blob/master/LICENSE
    :alt: MIT License

.. image:: https://img.shields.io/badge/Contributor%20Covenant-v1.4%20adopted-ff69b4.svg
    :target: CODE_OF_CONDUCT.md
    :alt: Contributor Covenant

Raincoat has you covered when you can't stay DRY. When the time comes where you HAVE to
copy code from a third party, Raincoat will let you know when this code is changed so
that you can update your local copy.


The problem
-----------

Lets say you're using a lib named ``umbrella`` which provides a function named
``use_umbrella`` and it reads as such :

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

This function does what it says it does, but it's not ideally splitted, depending on
your needs. For example, maybe at some point you realize you need each of the 3 separate
parts to be a function of its own. Or maybe you can't call time.sleep in your app. Or do
something else with the ``umbrella`` when it's open like dance with it.

It's also possible that you can't really make a pull request because your needs are
specific, or you don't have the time (that's sad but, hey, I know it happens) or any
other personnal reason. So what do you do? There's no real alternative. You copy and
paste the code, modify it to fit your needs and use your modified version. And whenever
there's a change to the upstream function, chances are you'll never know.


The solution
------------

Enter Raincoat.

You have made your own private copy of ``umbrella.use_umbrella`` (umbrella being at the
time at version 14.5.7) and it looks like this :

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

Now simply add a comment somewhere (preferably just after the docstring) that says
something like:

.. code-block:: python

    def dance_with_umbrella(umbrella):
        """
        I'm siiiiiinging in the rain !
        """
        # This code was adapted from the original umbrella.use_umbrella function
        # (we just changed the part inside the middle while loop)
        # Raincoat: pypi package: umbrella==14.5.7 path: umbrella/__init__.py element: use_umbrella

        ...

Now, install and run ``raincoat`` in your project:

.. code-block:: console

    $ pip install raincoat
	$ raincoat


It will:

- Grep the code for all ``# Raincoat:`` comments and for each comment:
- Look at the currently installed version of the lib (say, umbrella 16.0.3) (or, if not
  found, the latest version)
- Compare with the version in the Raincoat comment (here, 14.5.7)
- If they are different, download and pip install the specified version in a temp dir
  (using cached wheel as pip does by default, this should be quite fast in most cases)
- Locate the code using the provided path for both the downloaded and the currently
  installed versions
- Diff it
- Tell you if there's a difference (and mention the location of the original Raincoat
  comment)

Whether there is something to change or not, you've now verified your code with umbrella
16.0.3, so you can update manually the umbrella comment.

.. code-block:: python

	# Raincoat: pypi package: umbrella==16.0.3 path: umbrella/__init__.py element: use_umbrella"

Raincoat can be used like a linter, you can integrate it in CI, make it a tox target...


And beyond !
------------

Actually, the base principle of Raincoat can be extended to many other subjects than
PyPI packages. To fit this, Raincoat was written with a modular achitecture allowing
other kinds of Raincoat comments.

For now Raincoat comes with:

- *PyPI*: The module presented above
- *Django*: A module that checks if a given bug in Django for which you may have had
  to write a workaround is fixed in your (or the latest) version of Django. Syntax is :

.. code-block:: python

	# Raincoat: django ticket: #26976

- *PyGitHub* : Same as the PyPI module but using Github. It's useful if your upstream is
  a python package that's not on PyPI, like, say, the Python Standard Library itself.
  Say you want to know if the element ``Maildir._lookup`` in the file ``Lib/mailbox.py``
  changed on the master branch since commit 43ba8861. What you can do is:

.. code-block:: python

	# Raincoat: pygithub repo: python/cpython@43ba8861 branch: master path: Lib/mailbox.py element: Maildir._lookup

You can also create your own Raincoat comment checker.

You can head to the `Quickstart
<https://raincoat.readthedocs.io/en/stable/quickstart.html>`_ section for a general tour
or to the `How-To <https://raincoat.readthedocs.io/en/stable/howto_index.html>`_
sections for specific features. The `Discussions
<https://raincoat.readthedocs.io/en/stable/discussions.html>`_ section should hopefully
answer your questions. Otherwise, feel free to open an `issue
<https://github.com/ewjoachim/raincoat/issues>`_.

.. Below this line is content specific to the README that will not appear in the doc.
.. end-of-index-doc

Where to go from here
---------------------

The complete docs_ is probably the best place to learn about the project.

If you encounter a bug, or want to get in touch, you're always welcome to open a
ticket_.

.. _docs: https://raincoat.readthedocs.io/en/stable
.. _ticket: https://github.com/ewjoachim/raincoat/issues/new
