.. _configuring_models:


Setting up Models
=================

Model Mixin
-----------

You can optionally add ``data_validation.models.DataValidationMixin`` to your model to provide some extra properties for querying validation results

.. code-block:: python

    from data_validation.models import DataValidationMixin

    class MyModel(DataValidationMixin, models.Model):
        pass

See :ref:`module-data_validation.models` for a full list of provided properties

Configuration
-------------

If you want more control over how each model is validated you can add a class to your model called ``DataValidationConfig`` (similar to ``Meta``)

.. code-block:: python

    class MyModel(models.Model):
        class DataValidationConfig:
            exclude = True
        ...

Below is the full list of available options

.. class:: DataValidationConfig

   .. attribute:: exclude
      :type: bool

      if True, the model will be excluded from data validation. You might want this if the model is a non-abstract base model in an inheritance hierarchy.

