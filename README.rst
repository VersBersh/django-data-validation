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

:sh:`git clone https://github.com/VersBersh/django-data-validation.git`

change to the django-data-validation directory and install with pip

:sh:`pip install .`

In your project, add :sh:`datavalidation` to `INSTALLED_APPS`:

.. code-block:: python

    INSTALLED_APPS = (
        ...
        "datavalidation.apps.DataValidationConfig",
        ...
    )

To enable the admin run collectstatic in your project directory

:sh:`$YOUR_PROJECT_FOLDER/manage.py collectstatic`


Usage
-----

On any django model that has data that you would like to validate, add a method decorated
with :py:`@data_validator` that returns :py:`PASS, FAIL` or :py:`NA`.

.. code-block:: python

    from datavalidation import data_validator, PASS, FAIL, NA
    from django.db import models


    class YourModel(models.Model):
        ...
        start_time = models.DateTimeField()
        end_time = models.DateTimeField(blank=True, null=True)

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

:sh:`./manage.py run_data_validation`

or for a specific model

:sh:`./manage.py run_data_validation --models app_label.model_name`


more documentation to come...
