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

If you want more control over how each model is validated you can add a class to your model called that inherits from ``data_validation.config.Config`` (similar to ``Meta``)

.. code-block:: python

    from data_validation.config import Config

    class MyModel(models.Model):
        # the name of the class is not important
        class DataValidationConfig(Config):
            exclude = True
        ...

See :ref:`module-data_validation.config` for the full list of options available



