from datavalidation.config import Config

from .base import BaseModel


class Parent(BaseModel):
    pass


class ProxyModel(Parent):
    class Meta:
        proxy = True

    class TestData:
        NO_GENERATE = True  # don't generate records for this model during testing


class ExcludedModel(Parent):
    """ test that excluded models get excluded """
    class DVConfig(Config):
        exclude = True

    class TestData:
        NO_GENERATE = True


class ModelWithExcludedParent(ExcludedModel):
    class TestData:
        NO_GENERATE = True
