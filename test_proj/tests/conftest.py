from typing import Type

from django.db import models
import pytest

from animalconference.models import Animal, Seminar
from datavalidation.logging import logger
from datavalidation.registry import REGISTRY, ValidatorInfo
from datavalidation.results import SummaryEx
from datavalidation.runners import ModelValidationRunner


# noinspection PyUnusedLocal
@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """ add Validators to the test database """
    with django_db_blocker.unblock():
        REGISTRY.sync_to_db()


@pytest.fixture(scope="session")
def valid_animals(django_db_blocker):
    """ add 100 valid Animals to the test database """
    # setup
    with django_db_blocker.unblock():
        count = Animal.objects.count()
        if count == 0:
            Animal.objects.populate_database(100)
        elif count != 100:
            logger.cwarning("Animal count:", count)
            raise AssertionError("something went wrong with --reuse-db")


@pytest.fixture(scope="session")
def valid_seminars(django_db_blocker):
    """ add 10 valid Seminars to the test database """
    with django_db_blocker.unblock():
        count = Seminar.objects.count()
        if count == 0:
            Seminar.objects.populate_database(10)
        elif count != 10:
            logger.cwarning(count)
            raise AssertionError("something went wrong with --reuse-db")


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
