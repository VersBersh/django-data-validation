from django.apps import AppConfig

from .registry import update_registry


class DataValidationConfig(AppConfig):
    name = 'datavalidation'
    verbose_name = 'Django Data Validation'

    def ready(self):
        update_registry()
