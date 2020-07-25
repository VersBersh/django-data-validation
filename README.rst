.. role:: sh(code)
    :language: bash

.. role:: py(code)
    :language: python


DJANGO-DATA-VALIDATION
++++++++++++++++++++++

.. image:: https://readthedocs.org/projects/django-data-validation/badge/?version=latest
   :target: https://django-data-validation.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

** :warning: this app is still in alpha. expect breaking changes :warning: **

A Django app to manage the validation of your data. Inspired by `django-data-tests <https://github.com/andrewbird2/django-data-tests>`_

read the documentation: `<https://django-data-validation.readthedocs.io>`_

write tests on your Django models and view the summary in the admin

.. image:: https://raw.githubusercontent.com/VersBersh/django-data-validation/master/screenshot.png
    :width: 100%
    :alt: screenshot of the admin page

run the validation when adding/changing an object via django admin

.. image:: https://raw.githubusercontent.com/VersBersh/django-data-validation/master/screenshot2.png
    :width: 100%
    :alt: screenshot of a default admin change form

.. quick-start-marker

.. role:: sh(code)
    :language: bash

.. role:: py(code)
    :language: python


Quick Start
===========

Requirements
------------

- python >= 3.6
- django >= 2.2
- djangorestframework (tested against 3.11)


Installation
------------

clone the repo

.. code-block:: bash

    git clone https://github.com/VersBersh/django-data-validation.git

change to the django-data-validation directory and install with pip

.. code-block:: bash

    pip install .

In your project, add :py:`rest_framework` and :py:`datavalidation` to :py:`INSTALLED_APPS`

.. code-block:: python

    INSTALLED_APPS = (
        ...
        "rest_framework",
        "datavalidation.apps.DataValidationConfig",
        ...
    )

from your project directory run the database migrations

.. code-block:: bash

    ./manage.py migrate datavalidation

When running the django-admin server the static files for the datavalidation admin will be served automatically (assuming :py:`"django.contrib.staticfiles"` is in :py:`INSTALLED_APPS`). Otheriwse, you should also run

.. code-block:: bash

    ./manage.py collectstatic


Basic Usage
-----------

On any django model that has data that you would like to validate, add a method decorated with :py:`@data_validator` that returns :py:`PASS`, :py:`FAIL` or :py:`NA`. For instance if you have a model with a start and end time, you can add a data_validator to check that the start time is always before the end time

.. code-block:: python

    from django.db import models
    from datavalidation import data_validator, PASS, FAIL, NA

    class YourModel(models.Model):
        ...
        start_time = models.DateTimeField()
        end_time = models.DateTimeField(blank=True, null=True)
        ...

        @data_validator
        def check_start_time(self):
            """ check that the start time is before end time """
            if self.end_time is None:
                return NA("end time not set")
            elif self.start_time < self.end_time:
                return PASS
            else:
                return FAIL("end time is before start time!")


To run the validation for all models

.. code-block:: bash

    ./manage.py validate

or for a specific model

.. code-block:: bash

    ./manage.py validate yourapp.YouModel

.. nb. the :ref: directive won't work from the readme so we have to link directly

See `Writing Data Validators <https://django-data-validation.readthedocs.io/en/latest/data_validators.html>`_ for more details and examples of data validators

Optionally, you can add the ``data_validaiton.models.DataValidationMixin`` to your models to provide some additional methods for querying the validation results

.. code-block:: python

    from datavalidation.models import DataValidationMixin

    class YouModel(DataValidationMixin, models.Model):
        ...

    # in a shell
    print(YouModel.datavalidation_status)
    >>> Status.PASSING  # hopefully :)


Finally, you can also add ``data_validaiton.admin.DataValidationMixin`` to your django admin classes to review the data in the admin. See `Setting up the Admin <https://django-data-validation.readthedocs.io/en/latest/admin.html>`_ for details.
