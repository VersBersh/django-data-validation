.. _contributing:

Contributing
============

Contributions are more than welcome!


Types of Contributions
----------------------

Report Bugs or Request Features
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

On github: `<https://github.com/VersBersh/django-data-validation/issues>`_

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

Fix Bugs or Implement Features
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Look through the GitHub issues for bugs/features

There is also a `Trello Board <https://trello.com/b/AULMXnTC/django-data-validation>`_ with some ideas that i'd like to implement (new idea - migrate trello to github)


Development Setup (Linux)
-------------------------

Django-data-validation is developed on Ubuntu-18.04, but will probably work on macOS. If anyone uses this package at all, I might consider making it available on Windows.

1. Fork the `django-data-validation` repo on GitHub.
2. Clone your fork locally
3. Set up a virtual environment and activate it. Optional: I high recommend `pyenv <https://github.com/pyenv/pyenv>`_ for managing different python versions. `pyenv-virtualenv <https://github.com/pyenv/pyenv-virtualenv>`_ is also a nice way to manage your virtual environments. If using pyenv and virtualenv you can write:

.. code-block:: bash

    pyenv virtualenv 3.6.9 django-data-validation
    source "$PYENV_ROOT/versions/django-data-validation/bin/activate"

3. run the setup script for development (this will add the pre-commit hooks, install python dependencies, setup node, and add a .pth file to site-packages to make the directories discoverable by python)

.. code-block:: bash

    cd ./django-data-tests
    chmod +x ./setup/dev_setup.sh
    ./setup/dev_setup.sh

4. Optional: if you want to use a specific database in the django test project, create a `./test_proj/local_settings.py` file with the ``DATABAESS`` config. I am using postgres, but `settings.py` will default to sqlite3


Pull Request Guidelines
-----------------------

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests
2. If the pull request adds functionality, the docs should be updated.
3. flake8 and pytest are passing
