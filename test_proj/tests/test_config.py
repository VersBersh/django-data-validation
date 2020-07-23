from typing import TYPE_CHECKING

from datavalidation.config import Config, get_config
from django.db import models

if TYPE_CHECKING:
    _Base = models.Model
else:
    _Base = object


def test_config_inheritance():
    """ test that configs are not inheritable """
    class Base(_Base):
        class DataValidationConfig(Config):
            exclude = True

    class Child(Base):
        pass

    assert get_config(Base) is Base.DataValidationConfig
    assert get_config(Base).exclude is True
    assert get_config(Child) is Config


def test_bad_config():
    """ test that adding a bad config options raises an error """
    try:
        class Base(_Base):
            class DataValidation(Config):
                foobar = True
        assert False, "expected an exception"
    except ValueError:
        pass
