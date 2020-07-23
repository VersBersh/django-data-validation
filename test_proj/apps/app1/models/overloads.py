from datavalidation import data_validator, PASS, FAIL, NA

from .base import BaseModel

import sys
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))


class Overloaded(BaseModel):

    @data_validator
    def instancemethod_first(self):
        """ tests: overloading a function (instance method first) """
        logger.info("return_bool instance method")
        if self.foobar is None:
            return NA
        return self.foobar < 10

    @instancemethod_first.overload
    @classmethod
    def instancemethod_first(cls):
        """ tests: overloading a function (instance method first) """
        logger.info("return_bool class method")
        return cls.objects.filter(foobar__gte=10).count() == 0

    @data_validator
    @classmethod
    def classmethod_first(cls):
        """ tests: overloading a function (class method first) """
        logger.info("return_result class method")
        if cls.objects.filter(foobar__gte=10).count() == 0:
            return PASS
        return FAIL

    @classmethod_first.overload
    def classmethod_first(self):
        """ tests: overloading a function (class method first) """
        logger.info("return_result instance method")
        if self.foobar is None:
            return NA
        elif self.foobar < 10:
            return PASS
        return FAIL
