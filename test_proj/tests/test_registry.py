from app1.models import TestModel
from datavalidation.registry import REGISTRY


def test_registry():
    """ check that the REGISTRY contains the models """
    assert TestModel in REGISTRY

    model_info = REGISTRY[TestModel]
    assert model_info.app_label == TestModel._meta.app_label
    assert model_info.model_name == TestModel.__name__
    validator = TestModel.check_foobar.__name__
    assert isinstance(model_info.validators, dict)
    assert validator in model_info.validators

    valinfo = model_info.validators[validator]
    assert valinfo.model_info is model_info
    assert valinfo.method_name == validator
    assert valinfo.description == "check that foobar is less than 10"
    assert valinfo.instance_method is not None
    assert valinfo.class_method is None
    assert valinfo.select_related == set()
    assert valinfo.prefetch_related == set()
