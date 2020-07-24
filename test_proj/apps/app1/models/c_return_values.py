from datavalidation import data_validator, PASS, FAIL, NA, Summary
from datavalidation.models import DataValidationMixin

from .base import BaseModel


class CReturnValues(DataValidationMixin, BaseModel):
    """ Class Method Data Validator Return Values

    tests: valid return values for class method validators
    """
    @data_validator
    @classmethod
    def returning_result(cls):
        """ tests: returning PASS/FAIL """
        if cls.objects.filter(foobar__gte=10).count() == 0:
            return PASS
        return FAIL

    @data_validator
    @classmethod
    def returning_bool(cls):
        """ tests: returning a bool """
        return cls.objects.filter(foobar__gte=10).count() == 0

    @data_validator
    @classmethod
    def returning_queryset(cls):
        """ tests: returning a queryset """
        return cls.objects.filter(foobar__gte=10)

    @data_validator
    @classmethod
    def returning_list_of_models(cls):
        """ tests: returning a list """
        return list(cls.objects.filter(foobar__gte=10))

    @data_validator
    @classmethod
    def returning_list_of_model_ids(cls):
        """ tests: returning a list of ids """
        return cls.objects.filter(foobar__gte=10).values_list("id", flat=True)

    @data_validator
    @classmethod
    def returning_summary(cls):
        return Summary(
            num_passing=cls.objects.filter(foobar__lt=10).count(),
            num_na=cls.objects.filter(foobar__isnull=True).count(),
            failures=cls.objects.filter(foobar__gte=10)
        )

    @data_validator
    @classmethod
    def returning_bad_summary(cls):
        return Summary(
            failures=True  # noqa
        )

    @data_validator
    @classmethod
    def returning_na(cls):
        """ tests: returning NA (exception expected) """
        return NA

    @data_validator
    @classmethod
    def returning_none(cls):
        """ tests: returning None (exception expected) """
        return None

    @data_validator
    @classmethod
    def raising_exception(cls):
        """ tests: raising an exception """
        raise ValueError("An Error!")
