from animalconference.models import Animal, Seminar
from datavalidation.registry import REGISTRY, data_validator


def test_decorator():
    """ check that data_validator fails when decorating a function outside
        of a class
    """
    try:
        @data_validator
        def test():
            pass
        assert False, "expected an exception"
    except ValueError as e:
        assert e.args == ("data validators must be methods of a class",)


def test_registry():
    """ check that the REGISTRY contains the models """
    assert Animal in REGISTRY
    assert Seminar in REGISTRY

    model_info = REGISTRY[Animal]
    assert model_info.app_label == "animalconference"
    assert model_info.model_name == "Animal"
    assert isinstance(model_info.validators, dict)
    assert "check_alliteration" in model_info.validators

    valinfo = model_info.validators["check_alliteration"]
    assert valinfo.model_info is model_info
    assert valinfo.method_name == "check_alliteration"
    assert valinfo.description == "test that names are alliterations"
    assert valinfo.is_class_method is False
    assert valinfo.select_related == set()
    assert valinfo.prefetch_related == set()
