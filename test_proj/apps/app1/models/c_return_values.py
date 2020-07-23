from datavalidation import data_validator, PASS, FAIL, NA, Summary

from .base import BaseModel


class CReturnValues(BaseModel):
    """ Class Method Data Validator Return Values

    tests: valid return values for class method validators
    """
    @classmethod
    @data_validator
    def returning_result(cls):
        """ tests: returning PASS/FAIL """
        if cls.objects.filter(foobar__gte=10).count() == 0:
            return PASS
        return FAIL

    @classmethod
    @data_validator
    def returning_bool(cls):
        """ tests: returning a bool """
        return cls.objects.filter(foobar__gte=10).count() == 0

    @classmethod
    @data_validator
    def returning_queryset(cls):
        """ tests: returning a queryset """
        return cls.objects.filter(foobar__gte=10)

    @classmethod
    @data_validator
    def returning_list_of_models(cls):
        """ tests: returning a list """
        return list(cls.objects.filter(foobar__gte=10))

    @classmethod
    @data_validator
    def returning_list_of_model_ids(cls):
        """ tests: returning a list of ids """
        return cls.objects.filter(foobar__gte=10).values_list("id", flat=True)

    @classmethod
    @data_validator
    def returning_summary(cls):
        return Summary(
            num_passing=10,
            num_na=11,
            failures=[1]
        )

    @classmethod
    @data_validator
    def returning_bad_summary(cls):
        return Summary(
            failures=True  # noqa
        )

    @classmethod
    @data_validator
    def returning_na(cls):
        """ tests: returning NA (exception expected) """
        return NA

    @classmethod
    @data_validator
    def returning_none(cls):
        """ tests: returning None (exception expected) """
        return None

    @classmethod
    @data_validator
    def raising_exception(cls):
        """ tests: raising an exception """
        raise ValueError("An Error!")
