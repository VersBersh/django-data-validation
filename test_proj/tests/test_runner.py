from unittest import mock

from django.core.management import call_command
import pytest

from app1.models import TestModel
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
        ModelValidationRunner(TestModel, method_names=["not_a_method"]).run()
        assert False, "expected as exception"
    except ValueError as e:
        assert e.args == ("not_a_method is not a data validator on TestModel",)


@pytest.mark.django_db
def test_model_runner_cli_success():
    """ test ./manage.py validate app1.TestModel """
    with mock.patch("sys.exit") as mocked_exit:
        call_command("validate", "app1.TestModel")
        mocked_exit.assert_called_with(0)


@pytest.mark.django_db
def test_model_runner_cli_failure():
    """ test ./manage.py run_data_validation

     Some tests raise an exceptions so this should fail (exit_code==1)
    """
    with mock.patch("sys.exit") as mocked_exit:
        call_command("validate")
        mocked_exit.assert_called_with(1)


@pytest.mark.django_db
def test_object_runner():
    """ test the ObjectValidationRunner """
    validator = Validator.objects.get(
        app_label=TestModel._meta.app_label,
        model_name=TestModel.__name__,
        method_name=TestModel.check_foobar.__name__,
    )
    assert validator.status == Status.UNINITIALIZED

    obj_pass = TestModel.objects.first()
    result = ObjectValidationRunner(obj_pass).run()
    assert result is True

    validator.refresh_from_db()
    assert validator.status == Status.PASSING

    obj_fail, = TestModel.objects.generate(failing=1)
    result = ObjectValidationRunner(obj_fail).run()
    assert result is False

    validator.refresh_from_db()
    assert validator.status == Status.FAILING
