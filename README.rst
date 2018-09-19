=======
Insight
=======

Insight project.


* Free software: BSD license


Features
--------

* TODO


Requirements
------------

Package assumes you have API keys:

* ``FLICKR_API_KEY`` - Flickr API key
* ``FLICKR_API_SECRET`` - Flickr API secret
* ``GMAPS_API_KEY`` - Google Maps API key
* ``NOMINATIM_USER_AGENT`` - `Nominatim <https://wiki.openstreetmap.org/wiki/Nominatim>`_
  user agent (a string with your project name and e-mail address).

within a module that can be imported with ``import secrets``.  I recommend
running the code in a virtualenv, and adding a ``secrets.py`` file in a folder
included in the virtualenv's path (see `adding .pth files
<https://docs.python.org/3/install/index.html#modifying-python-s-search-path>`_).

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
