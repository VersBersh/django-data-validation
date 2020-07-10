from datetime import datetime, timedelta as td

import pytest

from animalconference.models import Seminar
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


# noinspection PyUnusedLocal
@pytest.fixture(scope="module", autouse=True)
def valid_seminars(valid_seminars):
    """ autouse valid_animals fixture """
    pass


def test_check_host_is_carnivorous():
    summary = run_validator(Seminar, "check_host_is_carnivorous")
    assert summary == SummaryEx(
        status=Status.PASSING,
        num_passing=10,
    ).complete()


def test_check_start_time_before_end_time():
    seminar = Seminar.objects.test_create(start_time=datetime.now(),
                                          end_time=datetime.now()-td(hours=1))
    summary = run_validator(Seminar, "check_start_time_before_end_time")
    logger.warning(summary.failures)
    logger.warning(summary.pretty_print())
    assert summary == SummaryEx(
        status=Status.FAILING,
        num_passing=None,
        num_na=None,
        num_allowed_to_fail=None,
        failures=[seminar.id]
    ).complete()


def test_check_max_attendees():
    summary = run_validator(Seminar, "check_max_attendees")
    assert summary == SummaryEx(
        status=Status.PASSING,
        num_passing=10
    ).complete()


def test_instancemethod_hits_an_exception():
    summary = run_validator(Seminar, "check_instancemethod_hits_an_exception")
    assert summary.status == Status.EXCEPTION
    assert summary.num_passing is None
    assert summary.num_na is None
    assert summary.num_allowed_to_fail is None
    assert summary.failures is None
    assert summary.exception_info["exc_type"] == "ValueError('instancemethod hit an exception',)"  # noqa E501
    assert isinstance(summary.exception_info["exc_traceback"], str)


def test_classmethod_hits_an_exception():
    summary = run_validator(Seminar, "check_classmethod_hits_an_exception")
    assert summary.status == Status.EXCEPTION
    assert summary.num_passing is None
    assert summary.num_na is None
    assert summary.num_allowed_to_fail is None
    assert summary.failures is None
    assert summary.exception_info["exc_type"] == "ValueError('classmethod hit an exception',)"  # noqa E501
    assert "exc_traceback" in summary.exception_info


def test_check_return_none():
    summary = run_validator(Seminar, "check_return_none")
    assert summary.status == Status.EXCEPTION
    assert summary.num_passing is None
    assert summary.num_na is None
    assert summary.num_allowed_to_fail is None
    assert summary.failures is None
    assert summary.exception_info["exc_type"].startswith("TypeError")
    assert "exc_obj_pk" in summary.exception_info


def test_check_return_silent():
    summary = run_validator(Seminar, "check_return_silent")
    assert summary.status == Status.EXCEPTION
    assert summary.num_passing is None
    assert summary.num_na is None
    assert summary.num_allowed_to_fail is None
    assert summary.failures is None
    assert summary.exception_info["exc_type"].startswith("TypeError")


def test_check_return_inconsistent_summary():
    summary = run_validator(Seminar, "check_return_inconsistent_summary")
    logger.info(summary)
    assert summary.status == Status.EXCEPTION
    assert summary.num_passing is None
    assert summary.num_na is None
    assert summary.num_allowed_to_fail is None
    assert summary.failures is None
    assert summary.exception_info["exc_type"].startswith("TypeError")
