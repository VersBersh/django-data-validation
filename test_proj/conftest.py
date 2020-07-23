from typing import Type

from django.core.management import call_command
from django.db import models
import pytest

from datavalidation.registry import REGISTRY, ValidatorInfo
from datavalidation.results import SummaryEx
from datavalidation.runners import ModelValidationRunner

from django.test import TestCase, TransactionTestCase

TestCase.databases = ("default", "postgres2")
TransactionTestCase.databases = ("default", "postgres2")


# noinspection PyUnusedLocal
@pytest.fixture(scope="package")
def django_db_setup(django_db_setup, django_db_blocker):
    """ add Validators to the test database """
    with django_db_blocker.unblock():
        REGISTRY.sync_to_db()
        call_command("add_test_data", 20, "--exact")


def run_validator(model: Type[models.Model], method_name: str) -> SummaryEx:
    """ helper method to run validation for a single method """
    runner = ModelValidationRunner(model, method_names=[method_name])
    result = runner.run()
    assert len(result) == 1
    assert len(result[0]) == 2

    valinfo, summary = result[0]
    assert isinstance(valinfo, ValidatorInfo)
    assert isinstance(summary, SummaryEx)
    return summary
