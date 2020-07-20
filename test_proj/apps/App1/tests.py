import pytest

from datavalidation.results import SummaryEx, Status
from .models import Model1
from pytest_utils import run_validator


@pytest.fixture(scope="module")
def model1(django_db_blocker):
    """ add all (6) habitats to the database """
    with django_db_blocker.unblock():
        Model1.generate(passing=10)


def test_validator_1(model1):
    summary = run_validator(Model1, "validator_1")
    assert summary == SummaryEx(
        status=Status.PASSING,
        num_passing=10,
        num_na=0,
        num_allowed_to_fail=0,
    )


def test_validator_2(model1):
    _, failing, _ = Model1.generate(failing=1)
    summary = run_validator(Model1, "validator_2")
    assert summary == SummaryEx(
        status=Status.FAILING,
        num_passing=10,
        num_na=0,
        num_allowed_to_fail=0,
        failures=failing
    )


def test_validator_3(model1):
    summary = run_validator(Model1, "validator_3")
    assert summary.status == Status.EXCEPTION
    assert summary.num_passing is None
    assert summary.num_na is None
    assert summary.num_allowed_to_fail is None
    assert summary.failures is None
    assert summary.exception_info["exc_type"].startswith("TypeError")
    assert "exc_obj_pk" in summary.exception_info

