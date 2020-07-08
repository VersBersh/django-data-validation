.. role:: sh(code)
    :language: bash

.. role:: py(code)
    :language: python


DJANGO-DATA-VALIDATION
++++++++++++++++++++++

A Django app to manage the validation of your data.

Quickstart
==========

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

    ./manage.py migrate datavaliation

When running the django-admin server the static files for the datavalidation admin will
be served automatically (assuming :py:`"django.contrib.staticfiles"` is in
:py:`INSTALLED_APPS`). If you're serving static files yourself you should run

.. code-block:: bash

    ./manage.py collectstatic

to copy the static files to :py:`STATIC_ROOT`

Usage
-----

On any django model that has data that you would like to validate, add a method decorated
with :py:`@data_validator` that returns :py:`PASS`, :py:`FAIL` or :py:`NA`. For instance
if you have a model with a start and end time, you can add a data_validator to check that
the start time is always before the end time

.. code-block:: python

    from datavalidation import data_validator, PASS, FAIL, NA
    from django.db import models


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
                return FAIL


To run the validation for all models

.. code-block:: bash

    ./manage.py run_data_validation

or for a specific model

.. code-block:: bash

    ./manage.py run_data_validation --models <app_label>.<model_name>


more documentation to come...
