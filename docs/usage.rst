#####
Usage
#####

Command line tool
=================

Up to date usage information is accessible with the command line interface by using

.. code-block:: bash

	raincoat --help


Raincoat comments
=================

Raincoat will detect comments in your code, that look like this :

.. code-block:: python

	# Raincoat: package "PACKAGE_NAME==VERSION" path "PATH" "OBJECT_NAME"

Where :

- ``PACKAGE_NAME`` is the name you would use with pip
- ``VERSION`` is required (note : it can be tempting to imagine that other oprators are available besides ``==``, it's not the case)
- ``PATH`` is the path between the place where pip would install a package (usually ``site-packages``) and the file containing the definition you want to check. It starts with the top module name (which in some cases is different from the package name, I know, it's frustrating.)
- ``OBJECT_NAME`` is the name of either a function, a class or a method. For methods, the expected format is ``ClassName.method_name``
