import pytest

from animalconference.models import Animal
from datavalidation.results import Status, SummaryEx
from ..conftest import run_validator

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


pytestmark = pytest.mark.django_db


# noinspection PyUnusedLocal
@pytest.fixture(scope="module", autouse=True)
def django_db_setup(django_db_setup):
    """ autouse django_db_setup fixture """
    pass


# noinspection PyUnusedLocal
@pytest.fixture(scope="module", autouse=True)
def valid_animals(valid_animals):
    """ autouse valid_animals fixture """
    pass


def test_check_alliteration():
    failure = Animal.objects.test_create(species="Ant", name="Bob")
    summary = run_validator(Animal, "check_alliteration")
    assert summary == SummaryEx(
        status=Status.FAILING,
        num_passing=100,
        num_na=0,
        num_allowed_to_fail=0,
        failures=[failure.id]
    ).complete()


def test_check_carnivorous():
    failure1 = Animal.objects.test_create(carnivorous=True, prey=[])
    failure2 = Animal.objects.test_create(carnivorous=False, prey=[failure1])
    summary = run_validator(Animal, "check_carnivorous")
    assert summary == SummaryEx(
        status=Status.FAILING,
        num_passing=100,
        num_na=0,
        num_allowed_to_fail=0,
        failures=[failure1.id, failure2.id]
    ).complete()


def test_check_no_cannibals():
    allowed_to_fail = Animal.objects.test_create(species="Mantis")
    summary = run_validator(Animal, "check_no_cannibals")
    assert summary == SummaryEx(
        status=Status.PASSING,
        num_passing=100,
        num_na=0,
        num_allowed_to_fail=1,
        failures=[allowed_to_fail.id]
    ).complete()


def test_check_predator_heirarchy():
    prey = Animal.objects.filter(predator_index__lt=10)[:2]
    predator = Animal.objects.test_create(
        carnivorous=True, predator_index=10, prey=prey
    )
    failure = Animal.objects.test_create(
        carnivorous=True, predator_index=2, prey=[predator]
    )
    summary = run_validator(Animal, "check_predator_heirarchy")
    assert summary == SummaryEx(
        status=Status.FAILING,
        num_passing=summary.num_passing,
        num_na=summary.num_na,
        num_allowed_to_fail=0,
        failures=[failure.id]
    ).complete()
