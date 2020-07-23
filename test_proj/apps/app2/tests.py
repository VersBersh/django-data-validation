import pytest

from conftest import run_validator
from django.contrib.contenttypes.models import ContentType

from datavalidation.models import FailingObject
from datavalidation.results import SummaryEx
from .models import SecondDatabase


@pytest.mark.django_db
def test_second_database():
    failure = SecondDatabase.objects.generate(failing=1)
    summary = run_validator(SecondDatabase, method_name="test_foobar")
    assert summary == SummaryEx(
        num_passing=20, num_na=0, failures=failure
    ).complete()
    # assert the FailingObject table was updated
    ct = ContentType.objects.get_for_model(SecondDatabase)
    assert FailingObject.objects.using("default").filter(content_type=ct).count() == 1
