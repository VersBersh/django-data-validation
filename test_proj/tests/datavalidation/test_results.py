import pytest

from animalconference.models import Animal
from datavalidation.results import Status, SummaryEx, Summary


@pytest.mark.django_db
def test_summary_ex_instantiation():
    """ creation of SummaryEx from summaries and return values """
    # should not throw errors
    SummaryEx()
    SummaryEx().complete()
    SummaryEx(num_passing=1, num_na=2, num_allowed_to_fail=3, failures=[]).complete()
    SummaryEx(exception_info={}).complete()
    SummaryEx.from_return_value(True)
    SummaryEx.from_return_value(False)
    SummaryEx(status=Status.PASSING).complete()
    SummaryEx(failures=list(Animal.objects.all()[:2])).complete()

    # should throw errors
    try:
        SummaryEx(num_passing=None).complete()
        assert False, "expected an exception"
    except TypeError:
        pass

    try:
        SummaryEx(failures=True).complete()  # noqa
        assert False, "expected an exception"
    except TypeError:
        pass

    try:
        SummaryEx.from_summary(Summary(failures=None)).complete()  # noqa
        assert False, "expected an exception"
    except TypeError:
        pass


def test_summary_ex_equality():
    assert SummaryEx(num_passing=1) == SummaryEx(num_passing=1)
    assert SummaryEx(failures=[1, 2]) == SummaryEx(failures=[2, 1])
    assert (SummaryEx(exception_info={"exc_obj_id": 1})
            == SummaryEx(exception_info={"exc_obj_id": 1}))
    assert (SummaryEx.from_summary(Summary(num_passing=1, failures=[2]))
            == SummaryEx(num_passing=1, failures=[2]))

    assert SummaryEx(num_passing=1) != SummaryEx(num_passing=2)
    assert SummaryEx(num_passing=1) != SummaryEx(num_passing=None)
    assert SummaryEx(failures=[]) != SummaryEx(failures=None)
    assert SummaryEx(failures=[1, 2, 3]) != SummaryEx(failures=[2, 1])
    assert (SummaryEx(exception_info={"exc_type": "ValueError"})
            != SummaryEx(exception_info={"exc_type": "TypeError"}))
    assert (SummaryEx(exception_info={"exc_type": "ValueError"})
            != SummaryEx(exception_info=None))


def test_summary_ex_pretty_print():
    summary = SummaryEx(
        num_passing=1, num_na=2, failures=[3, 4]
    ).pretty_print()
    assert summary == (
        "PASSED: 1\n"
        "FAILED: 2\n"
        "NA: 2\n"
        "Allowed to Fail: 0\n"
        "Failing Ids: 3, 4"
    )

    summary = SummaryEx(
        num_passing=None, num_na=None, failures=[1, 2, 3, 4]
    ).pretty_print()
    assert summary == (
        "FAILED: 4\n"
        "Allowed to Fail: 0\n"
        "Failing Ids: 1, 2, 3..."
    )

    summary = SummaryEx(
        num_passing=1,
        exception_info={"exc_type": "ValueError()", "exc_obj_pk": 1}
    ).pretty_print()
    assert summary == "EXCEPTION: ValueError() (object pk=1)"
