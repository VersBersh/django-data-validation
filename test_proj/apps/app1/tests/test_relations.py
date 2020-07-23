from datavalidation.results import SummaryEx, PASS
import pytest

from app1.models.relations import RelatedFields
from conftest import run_validator

import logging


pytestmark = pytest.mark.django_db


def assert_no_warnings(caplog):
    """ assert no warnings were raised """
    for name, level, message in caplog.record_tuples:
        if level >= logging.WARNING:
            assert False, f"unexpected warning: {message}"


def test_select_related_o2o(caplog):
    summary = run_validator(RelatedFields, "select_related_o2o")
    assert summary == SummaryEx(num_passing=20).complete()
    assert_no_warnings(caplog)


def test_select_related_fkey(caplog):
    summary = run_validator(RelatedFields, "select_related_fkey")
    assert summary == SummaryEx(num_passing=20).complete()
    assert_no_warnings(caplog)


def test_select_related_rev_fkey(caplog):
    summary = run_validator(RelatedFields, "prefetch_related_rev_fkey")
    assert summary == SummaryEx(num_passing=20).complete()
    assert_no_warnings(caplog)


def test_select_related_m2m(caplog):
    summary = run_validator(RelatedFields, "prefetch_related_m2m")
    assert summary == SummaryEx(num_passing=20).complete()
    assert_no_warnings(caplog)


def test_bad_related_names(caplog):
    summary = run_validator(RelatedFields, "bad_related_names")
    assert summary == SummaryEx(num_passing=20).complete()
    for name, level, message in caplog.record_tuples:
        if name == "datavalidation" and level == logging.WARNING:
            break
    else:
        assert False, "expected a warning about related names"


def test_useless_select_related(caplog):
    summary = run_validator(RelatedFields, "useless_select_related")
    print(summary.__dict__)
    assert summary == SummaryEx.from_return_value(PASS).complete()
    assert_no_warnings(caplog)
