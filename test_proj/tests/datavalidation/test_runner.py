from unittest import mock

from django.core.management import call_command
import pytest

from animalconference.models import Animal
from datavalidation.models import Validator
from datavalidation.runner import ModelValidationRunner


def test_runner_with_bad_model():
    """ check that ModelValidationRunner handles bad input """
    try:
        ModelValidationRunner(Validator).run()
        assert False, "expected an exception"
    except ValueError as e:
        assert e.args == ("no data validation methods on model Validator",)


def test_runner_with_bad_method():
    """ check that ModelValidationRunner handles bad input """
    try:
        ModelValidationRunner(Animal, method_names=["foobar"]).run()
        assert False, "expected as exception"
    except ValueError as e:
        assert e.args == ("foobar is not a data validator on Animal",)


@pytest.mark.django_db
def test_runner_cli_success(valid_animals):
    """ test ./manage.py run_data_validation --models animalconference.Animal

     the valid_animals fixture was loaded so this should pass
    """
    with mock.patch("sys.exit") as mocked_exit:
        call_command("run_data_validation", models=["animalconference.Animal"])
        mocked_exit.assert_called_with(0)


@pytest.mark.django_db
def test_runner_cli_failure(valid_animals):
    """ test ./manage.py run_data_validation

     Seminar model contains data_validators that hit exceptions, so this
     should fail (exit_code==1)
    """
    with mock.patch("sys.exit") as mocked_exit:
        call_command("run_data_validation")
        mocked_exit.assert_called_with(1)
