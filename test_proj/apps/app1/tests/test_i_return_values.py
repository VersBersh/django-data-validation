from datavalidation.results import SummaryEx
import pytest

from app1.models.i_return_values import IReturnValues
from conftest import run_validator


pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("num_failing, num_na", [
    (0, 0), (0, 1), (2, 0), (2, 1),
])
def test_returning_result(num_failing, num_na):
    failures = IReturnValues.objects.generate(failing=num_failing)
    IReturnValues.objects.generate(na=num_na)
    summary = run_validator(IReturnValues, "returning_result")
    assert summary == SummaryEx(
        num_passing=20,
        num_na=num_na,
        failures=failures
    ).complete()


@pytest.mark.parametrize("num_failing, num_na", [
    (0, 0), (0, 1), (2, 0), (2, 1),
])
def test_returning_bool(num_failing, num_na):
    failures = IReturnValues.objects.generate(failing=num_failing)
    IReturnValues.objects.generate(na=num_na)
    summary = run_validator(IReturnValues, "returning_bool")
    assert summary == SummaryEx(
        num_passing=20,
        num_na=num_na,
        failures=failures
    ).complete()


def test_allowed_to_fail():
    failures = IReturnValues.objects.generate(failing=10)
    IReturnValues.objects.generate(na=5)
    summary = run_validator(IReturnValues, "allowed_to_fail")
    assert summary == SummaryEx(
        num_passing=20,
        num_na=5,
        num_allowed_to_fail=10,
        failures=failures,
    ).complete()


def test_returning_none():
    summary = run_validator(IReturnValues, "returning_none")
    assert summary.exc_type.startswith("TypeError")
    assert summary.num_passing is None
    assert summary.num_na is None
    assert summary.num_allowed_to_fail is None
    assert summary.failures is None


def test_raising_exception():
    summary = run_validator(IReturnValues, "raising_exception")
    assert summary.exc_type.startswith("ValueError")
    assert summary.exc_traceback is not None
    assert summary.num_passing is None
    assert summary.num_na is None
    assert summary.num_allowed_to_fail is None
    assert summary.failures is None
