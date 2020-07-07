from animalconference.models import Animal

from datavalidation.models import Validator
from datavalidation.runner import ModelValidationRunner


def test_runner_with_bad_model():
    """ check that ModelValidationRunner handles bad input """
    try:
        ModelValidationRunner(Validator).run()
        assert False, "expected an exception"
    except ValueError as e:
        assert e.args == ("no data_validation methods on model Validator",)


def test_runner_with_bad_method():
    """ check that ModelValidationRunner handles bad input """
    try:
        ModelValidationRunner(Animal, method_names=["foobar"]).run()
        assert False, "expected as exception"
    except ValueError as e:
        assert e.args == ("foobar is not a data_validator on Animal",)
