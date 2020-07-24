from datavalidation.results import SummaryEx, Summary
import pytest

from app1.models.c_return_values import CReturnValues
from conftest import run_validator


pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("num_failing, num_na", [
    (0, 0), (0, 1), (2, 0), (2, 1),
])
def test_returning_result(num_failing, num_na):
    failures = CReturnValues.objects.generate(failing=num_failing)
    CReturnValues.objects.generate(na=num_na)
    summary = run_validator(CReturnValues, "returning_result")
    expected_status = SummaryEx(failures=failures).complete().status
    assert summary == SummaryEx(
        status=expected_status, num_passing=None, num_na=None,
        num_allowed_to_fail=None,
    ).complete()


@pytest.mark.parametrize("num_failing, num_na", [
    (0, 0), (0, 1), (2, 0), (2, 1),
])
def test_returning_bool(num_failing, num_na):
    failures = CReturnValues.objects.generate(failing=num_failing)
    CReturnValues.objects.generate(na=num_na)
    summary = run_validator(CReturnValues, "returning_bool")
    expected_status = SummaryEx(failures=failures).complete().status
    assert summary == SummaryEx(
        status=expected_status, num_passing=None, num_na=None,
        num_allowed_to_fail=None,
    ).complete()


@pytest.mark.parametrize("num_failing, num_na", [
    (0, 0), (0, 1), (2, 0), (2, 1),
])
def test_returning_queryset(num_failing, num_na):
    failures = CReturnValues.objects.generate(failing=num_failing)
    CReturnValues.objects.generate(na=num_na)
    summary = run_validator(CReturnValues, "returning_queryset")
    assert summary == SummaryEx.from_return_value(failures).complete()


@pytest.mark.parametrize("num_failing, num_na", [
    (0, 0), (0, 1), (2, 0), (2, 1),
])
def test_returning_list_of_models(num_failing, num_na):
    failures = CReturnValues.objects.generate(failing=num_failing)
    CReturnValues.objects.generate(na=num_na)
    summary = run_validator(CReturnValues, "returning_list_of_models")
    assert summary == SummaryEx.from_return_value(failures).complete()


@pytest.mark.parametrize("num_failing, num_na", [
    (0, 0), (0, 1), (2, 0), (2, 1),
])
def test_returning_list_of_model_ids(num_failing, num_na):
    failures = CReturnValues.objects.generate(failing=num_failing)
    CReturnValues.objects.generate(na=num_na)
    summary = run_validator(CReturnValues, "returning_list_of_model_ids")
    assert summary == SummaryEx.from_return_value(failures).complete()


def test_returning_summary():
    summary = run_validator(CReturnValues, "returning_summary")
    assert summary == SummaryEx.from_summary(Summary(
        num_passing=20, num_na=0, failures=[]
    )).complete()


def test_returning_bad_summary():
    summary = run_validator(CReturnValues, "returning_bad_summary")
    assert summary.exc_type.startswith("TypeError")
    assert summary.num_passing is None
    assert summary.num_na is None
    assert summary.num_allowed_to_fail is None
    assert summary.failures is None


def test_returning_na():
    summary = run_validator(CReturnValues, "returning_na")
    assert summary.exc_type.startswith("TypeError")
    assert summary.num_passing is None
    assert summary.num_na is None
    assert summary.num_allowed_to_fail is None
    assert summary.failures is None


def test_returning_none():
    summary = run_validator(CReturnValues, "returning_none")
    assert summary.exc_type.startswith("TypeError")
    assert summary.num_passing is None
    assert summary.num_na is None
    assert summary.num_allowed_to_fail is None
    assert summary.failures is None


def test_raising_exception():
    summary = run_validator(CReturnValues, "raising_exception")
    assert summary.exc_type.startswith("ValueError")
    assert summary.exc_traceback is not None
    assert summary.num_passing is None
    assert summary.num_na is None
    assert summary.num_allowed_to_fail is None
    assert summary.failures is None
