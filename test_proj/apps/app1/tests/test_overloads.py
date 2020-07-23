import pytest
from datavalidation import data_validator
from datavalidation.runners import ModelValidationRunner, ObjectValidationRunner

from app1.models import Overloaded


def test_bad_instancemethod_overloading():
    """ test that overloading an instance method with an instance method fails """
    try:
        class _Test:
            @data_validator
            def foo(self):
                pass

            @foo.overload
            def foo(self):
                pass

        assert False, "expected exception"
    except RuntimeError:
        pass


def test_bad_classmethod_overloading():
    """ test that overloading a class method with a class method fails """
    try:
        class _Test:
            @data_validator
            @classmethod
            def foo(cls):
                pass

            @foo.overload
            @classmethod
            def foo(cls):
                pass

        assert False, "expected exception"
    except RuntimeError:
        pass


def test_bad_naming():
    """ test that overloading a method with a different name fails """
    try:
        class _Test:
            @data_validator
            def foo(self):
                pass

            @foo.overload
            @classmethod
            def bar(cls):
                pass

        assert False, "expected exception"
    except ValueError:
        pass


@pytest.mark.django_db
def test_model_runner(caplog):
    """ test that the model validation runner uses the class methods from
        overloaded validators
    """
    summaries = ModelValidationRunner(Overloaded).run()
    assert len(summaries) == 3  # 2 overloaded + 1 from BaseModel
    messages = [
        message for name, level, message in caplog.record_tuples
        if name == "app1.models.overloads"
    ]
    assert len(messages) == 2  # the two overloaded function
    # the model validation runner should use the class methods where available
    assert all("class method" in msg for msg in messages)


@pytest.mark.django_db
def test_object_runner(caplog):
    """ test that the object validation runner uses the instance methods
        from overloaded validators
    """
    obj = Overloaded.objects.first()
    result = ObjectValidationRunner(obj).run(class_methods=True)
    assert result is True
    messages = [
        message for name, level, message in caplog.record_tuples
        if name == "app1.models.overloads"
    ]
    assert len(messages) == 2  # the two overloaded function
    # the object validation runner should use the instance methods where available
    assert all("instance method" in msg for msg in messages)
