from unittest import mock

from django.core.management import call_command
import pytest

from animalconference.models import Animal
from datavalidation.models import Validator
from datavalidation.results import Status
from datavalidation.runners import ModelValidationRunner, ObjectValidationRunner


def test_model_runner_with_bad_model():
    """ check that ModelValidationRunner handles bad input """
    try:
        ModelValidationRunner(Validator).run()
        assert False, "expected an exception"
    except ValueError as e:
        assert e.args == ("no data validation methods on model Validator",)


def test_model_runner_with_bad_method():
    """ check that ModelValidationRunner handles bad input """
    try:
        ModelValidationRunner(Animal, method_names=["foobar"]).run()
        assert False, "expected as exception"
    except ValueError as e:
        assert e.args == ("foobar is not a data validator on Animal",)


@pytest.mark.django_db
def test_model_runner_cli_success(valid_animals):
    """ test ./manage.py run_data_validation --models animalconference.Animal

     the valid_animals fixture was loaded so this should pass
    """
    with mock.patch("sys.exit") as mocked_exit:
        call_command("run_data_validation", models=["animalconference.Animal"])
        mocked_exit.assert_called_with(0)


@pytest.mark.django_db
def test_model_runner_cli_failure(valid_animals):
    """ test ./manage.py run_data_validation

     Seminar model contains data_validators that hit exceptions, so this
     should fail (exit_code==1)
    """
    with mock.patch("sys.exit") as mocked_exit:
        call_command("run_data_validation")
        mocked_exit.assert_called_with(1)


@pytest.mark.django_db
def test_object_runner(valid_animals):
    """ test the ObjectValidationRunner """
    validator = Validator.objects.get(
        app_label="animalconference",
        model_name="Animal",
        method_name="check_alliteration"
    )
    assert validator.status == Status.UNINITIALIZED

    animal = Animal.objects.first()
    result = ObjectValidationRunner(animal).run()
    assert result is True

    validator.refresh_from_db()
    assert validator.status == Status.PASSING

    animal = Animal.objects.test_create(name="Anna", species="Bat")
    result = ObjectValidationRunner(animal).run()
    assert result is False

    validator.refresh_from_db()
    assert validator.status == Status.FAILING
