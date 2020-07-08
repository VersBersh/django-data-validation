import pytest

from animalconference.models import Animal
from datavalidation.results import Status, SummaryEx, Summary


@pytest.mark.django_db
def test_summary_ex_instantiation():
    """ creation of SummaryEx from summaries and return values """
    # should not throw errors
    SummaryEx.from_return_value(True)
    SummaryEx.from_return_value(False)
    SummaryEx(status=Status.PASSING).complete()
    SummaryEx(num_failing=2, failures=list(Animal.objects.all()[:2])).complete()

    # should throw errors
    try:
        # needs num_failing
        SummaryEx(failures=list(Animal.objects.all()[:3])).complete()
        assert False, "excpected an exception"
    except AssertionError:
        pass

    try:
        SummaryEx(num_failing=1, failures=[1, 2]).complete()  # but this is not
        assert False, "expected an exception"
    except AssertionError:
        pass

    try:
        SummaryEx(failures=None).complete()  # noqa
        assert False, "expected an exception"
    except TypeError:
        pass

    try:
        SummaryEx.from_summary(Summary(failures=None)).complete()  # noqa
        assert False, "expected an exception"
    except TypeError:
        pass

    try:
        SummaryEx(num_passing=None).complete()
        assert False, "expected an exception"
    except TypeError:
        pass


def test_summary_ex_equality():
    assert SummaryEx(num_passing=1) == SummaryEx(num_passing=1)
    assert SummaryEx(failures=[1, 2]) == SummaryEx(failures=[2, 1])

    assert SummaryEx(num_passing=1) != SummaryEx(num_passing=2)
    assert SummaryEx(failures=[1, 2, 3]) != SummaryEx(failures=[2, 1])
    assert (SummaryEx(exception_info={"exc_type": "ValueError"})
            != SummaryEx(exception_info={"exc_type": "TypeError"}))
    assert (SummaryEx(exception_info={"exc_type": "ValueError"})
            != SummaryEx(exception_info=None))


def test_summary_ex_pretty_print():
    summary = SummaryEx(
        num_passing=1, num_failing=2, num_na=3, failures=[4, 5, 6, 7]
    ).pretty_print()
    assert summary == (
        "PASSED: 1\n"
        "FAILED: 2\n"
        "NA: 3\n"
        "Allowed to Fail: 0\n"
        "Failing Ids: 4, 5, 6..."
    )

    summary = SummaryEx(
        exception_info={"exc_type": "ValueError()", "exc_obj_pk": 1}
    ).pretty_print()
    assert summary == "EXCEPTION: ValueError() (object pk=1)"
