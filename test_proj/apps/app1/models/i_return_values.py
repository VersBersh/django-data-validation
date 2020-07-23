from datavalidation import data_validator, PASS, FAIL, NA

from .base import BaseModel


class IReturnValues(BaseModel):
    """ Instance Method Data Validator Return Values

    tests: valid return values for instance method validators
    """

    @data_validator
    def returning_result(self):
        """ tests: returning PASS/FAIL/NA """
        if self.foobar is None:
            return NA
        elif self.foobar < 10:
            return PASS
        return FAIL("foobar too large!")

    @data_validator
    def returning_bool(self):
        """ tests: returning a bool """
        if self.foobar is None:
            return NA
        return self.foobar < 10

    @data_validator
    def allowed_to_fail(self):
        if self.foobar is None:
            return NA
        elif self.foobar < 10:
            return PASS
        return FAIL("it's okay", allowed_to_fail=True)

    @data_validator
    def returning_none(self):
        """ tests: returning a None (exception expected) """
        return None

    @data_validator
    def raising_exception(self):
        """ tests: raising an exception """
        raise ValueError("An Error!")
