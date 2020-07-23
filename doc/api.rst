.. _api:

API Reference
=============

management commands
-------------------

**validate**

.. code-block:: bash

    ./manage.py validate [LABELS]

run the data validation.

``LABELS`` -- an (optional) space seperated list of labels of the form ``<app_label>``, ``<app_label>.<model_name>``, or ``<app_label>.<model_name>::<validator_name>``. If no labels are provided then all models are validated.



datavalidation
---------------

.. module:: data_validation


.. function:: data_validator(select_related=None, prefetch_related=None)

   A decorator that identifies a method on a django model as a data validator. The decorated method may be a regular (instance) method or a `@classmethod` on a django model. It must take only one parameter (`self` or `cls`) and return a validation result. See :ref:`data_validators` for examples.

   :param Union[None,str,List[str]] select_related: arguments to be passed to QuerySet.select_related
   :param Union[None,str,List[str]] prefetch_related: arguments to be passed to QuerySet.prefetch_related

   :returns: a function

.. class:: NA
.. class:: PASS
.. class:: FAIL

   values to be returned from data validators to signify Not Applicable, Passing, or Failing respectively.

   :param str comment: (FAIL only) an optional comment to return. You can also pass comments to ``PASS`` and ``NA`` but such objects are not stored to the database so the comment is discarded.
   :param bool allowed_to_fail: (FAIL only) if an object fails validation but it is allowed or expected to fail then you can pass ``FAIL(allowed_to_fail=True)``. A validator will not be considered to have failed if any objects that fail are marked allowed_to_fail.

.. class:: Summary

   A possible return value for a class method validator

   :param int num_na: the number of objects for which validation is not applicable
   :param int num_passing: the number of objects that pass validation
   :param Union[QuerySet,List[models.Model],List[int]] failures: a QuerySet, list of objects or their ids that fail validation. See :ref:`data_validators` for examples.


.. use cpp name space because there's no support for py:enum::
.. c:enum:: Status

    An Enum representing the validation status of a validator, model, or app

    .. c:enumerator::
      UNINITIALIZED
      PASSING
      FAILING
      EXCEPTION
      WARNING


datavalidation.admin
---------------------

.. module:: data_validation.admin

.. class:: DataValidationMixin

    Adds validation results to the django admin. See :ref:`admin` for details.


.. _module-data_validation.config:

datavalidation.config
----------------------

.. class:: Config

    Configuration options for data validation

   .. attribute:: exclude
      :type: bool

      if True, the model will be excluded from data validation. You might want this if the model is a non-abstract base model in an inheritance hierarchy.



.. _module-data_validation.models:

datavalidation.models
----------------------

.. module:: data_validation.models

.. class:: DataValidaitonMixin

    Provides methods to a django model to query the objects that fail data validation

    .. method:: datavalidaiton_results
       :property:

       :returns: the QuerySet objects that failed data validation. The QuerySet model is of type data_validation.models.FailingObject

    .. method:: datavalidation_passing
       :property:

       :returns: True if no objects fail validation (except those marked `allowed to fail`)

    .. method:: datavalidation_status
        :classmethod:

        :returns: the ``data_validaiton.results.Status`` of the model


datavalidation.runners
-----------------------

.. module:: data_validation.runners


.. class:: ModelValidationRunner(model[, method_names=None])

   Run all or a subset of data_validators for the given model

   :param Type[django.db.models.Model] model: the model to validate
   :param Optional[List[str]] method_names: the names of the data_validators to run. If None it will run all validators on the model

   .. method:: run([show_progress=False])

      start the validation runner

      :param bool show_progress: if True a progress bar will be displayed.


.. class:: ObjectValidationRunner(obj)

   Run all `instance methods` data_validators for a given object. (see :ref:`data_validators` for the destinction on instance and class method validators)

   :param django.db.models.Model obj: the object to validate

   .. method:: run()

      start the validation runner
