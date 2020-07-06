Discussions
===========

Caveats and Gotchas
-------------------

- The 2 elements you provide in path should be the location of the file when the
  package is installed (in most case, this should match the location of the file in the
  project repo) and the object defined in this file. This object can be a variable, a
  class, a function or a method.
- Your own customized (copied/pasted) version of the function will not be analyzed.
  In fact, you don't even have to place the Raincoat comment in the function that uses
  it.
- You may realize that raincoat works best if you can use some kind of pip cache.
- Raincoat does not run files (either your files or the package file). Package files
  are parsed and the AST is analyzed.
- If for any reason, several code objects are identically named in the file you
  analyze, there's no guarantee you'll get any specific one.
- The Django module uses the public GitHub API and does a few calls. This should not be
  a concern most of the time, but you may experience rate-limiting issues if Raincoat is
  launched from an IP that does a lot of calls to the GitHub API (e.g. Travis). In this
  case, from your Travis settings, set the environment variable
  ``RAINCOAT_GITHUB_TOKEN`` to ``username:github_token``, ``github_token being`` a token
  generated `here <https://github.com/settings/tokens>`_ with all checkboxes unchecked.
- So few people use Raincoat for now that you should expect a few bumps down the road.
  This being said, fire issues and pull requetes at will and I'll do my best to answer
  them in a timely manner.


Todos
-----

Things I'd like to add at some point

- An option to update a comment automatically
- A way to say you want your customized function to be diffed too (in case it's a
  close copy and you want to keep track of what you've modified)
- A way to access the original function without the process of downloading the whole
  package and installing it for nothing. We just want a single file of it.


Acknowledgments
---------------

This code is open-sourced and maintained by me (Joachim Jablon) during both my free time
and my time working at `PeopleDoc <http://people-doc.com>`_, based on an idea and a
first implemention made at `Smart Impulse <http://smart-impulse.com>`_. Kudos to these 2
companies.
