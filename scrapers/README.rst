The scrapers assume your Python environment have API keys:

* ``FLICKR_API_KEY`` - Flickr API key
* ``FLICKR_API_SECRET`` - Flickr API secret

within a module that can be imported with ``import secrets``.  I recommend
running the code in a virtualenv, and adding a ``secrets.py`` file in a folder
included in the virtualenv's path (see `adding .pth files
<https://docs.python.org/3/install/index.html#modifying-python-s-search-path>`_).