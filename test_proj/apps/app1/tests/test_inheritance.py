from datavalidation.registry import REGISTRY

from app1.models.inheritance import (
    ExcludedModel, ProxyModel, ModelWithExcludedParent
)


def test_proxy_model():
    """ proxy models should be included for validation """
    assert ProxyModel in REGISTRY


def test_excluded_model():
    """ models excluded via their config should not be included """
    assert ExcludedModel not in REGISTRY


def test_model_with_excluded_parent():
    """ models whos parents were excluded should still be included """
    assert ModelWithExcludedParent in REGISTRY
