from collections import defaultdict
import inspect
from typing import (
    Callable, DefaultDict, Dict, List, Optional,
    Sequence, Tuple, Type, Union
)

from dataclasses import dataclass, field
from django.db import models
from django.utils.functional import cached_property  # n.b. in functools from py3.7+

from .constants import MAX_DESCRIPTION_LEN
from .utils import is_class_method


@dataclass
class _PreLoadMethodInfo:
    """ information available about a model before all apps are loaded. """
    method_name: str
    select_related: Tuple[str] = field(default_factory=tuple)
    prefetch_related: Tuple[str] = field(default_factory=tuple)


@dataclass
class ValidatorInfo:
    """ information about a data validator. """
    model_info: "ModelInfo"
    method: Callable
    method_name: str
    description: str
    is_class_method: bool
    select_related: tuple
    prefetch_related: tuple

    def __str__(self):
        mi = self.model_info
        return f"{mi.app_label}.{mi.model_name}.{self.method_name}"

    def __hash__(self):
        return hash(str(self))

    @cached_property
    def validator_id(self) -> int:
        """ return the primary key of the corresponding ValidationMethod """
        from .models import Validator
        obj, _ = Validator.objects.update_or_create(
            method_name=self.method_name,
            defaults={
                "app_label": self.model_info.app_label,
                "model_name": self.model_info.model_name,
                "is_class_method": self.is_class_method,
                "description": self.description,
            }
        )
        return obj.id


@dataclass
class ModelInfo:
    """ information about a model with data validator methods. """
    model: Optional[Type[models.Model]]
    app_label: str
    model_name: str
    validators: Dict[str, ValidatorInfo] = field(default_factory=dict)

    def __str__(self):
        return f"{self.app_label}.{self.model_name}"

    def __hash__(self):
        return hash(str(self))

    @cached_property
    def content_type_id(self) -> int:
        from django.contrib.contenttypes.models import ContentType
        return ContentType.objects.get_for_model(self.model).id


# temporary registry for initialization
_REGISTRY: DefaultDict[Tuple[str, str], List[_PreLoadMethodInfo]] = defaultdict(list)

REGISTRY: Dict[Type[models.Model], ModelInfo] = {}


def data_validator(_method: Optional[Callable] = None,
                   *,
                   select_related: Union[Sequence, str, None] = None,
                   prefetch_related: Union[Sequence, str, None] = None,
                   ) -> Callable:
    """ decorator that marks a method as a data validator.

     Args:
         _method: the method to decorate. Passed by python automatically
            when using the decorator @data_validator without parenthesis
         select_related: an optional field name, or list of field names
            to include in the call to select_related on the queryset before
            iterating the queryset to speed up the execution of the
            validation (for classmethod data validators this does nothing)
         prefetch_related: the same as select_related, but for
            prefetch_related
    """
    if _method is None:
        return _data_validator(select_related, prefetch_related)
    else:
        if select_related is not None:
            raise TypeError("cannot specify select_related when the first "
                            "argument is a callable")
        if prefetch_related is not None:
            raise TypeError("cannot specify prefetch_related when the "
                            "first argument is a callable")
        return _data_validator()(_method)


def _data_validator(select_related: Union[Sequence, str, None] = None,
                    prefetch_related: Union[Sequence, str, None] = None,
                    ) -> Callable:
    """ add method pre-load info to _REGISTRY """
    if select_related is None:
        select_related = set()
    elif isinstance(select_related, str):
        select_related = (select_related,)
    else:
        select_related = tuple(select_related)

    if prefetch_related is None:
        prefetch_related = set()
    elif isinstance(prefetch_related, str):
        prefetch_related = (prefetch_related,)
    else:
        prefetch_related = tuple(prefetch_related)

    def decorator(method: Callable) -> Callable:
        global _REGISTRY
        method_name = method.__name__
        app_label = getattr(method, "__module__", "").split(".")[0]
        qualname = getattr(method, "__qualname__", "")
        # hack: methods defined on classes have "." in their qualified name,
        # and methods defined within other functions have "<locals>"
        if "." not in qualname or "<locals>" in qualname:
            raise ValueError("data validators must be methods of a class")
        model_name = qualname.split(".")[0]
        # nb. we cannot find the content types until all models are loaded,
        # so this just stores the app labels, model names and method names.
        _REGISTRY[(app_label, model_name)].append(_PreLoadMethodInfo(
            method_name=method_name,
            select_related=select_related,
            prefetch_related=prefetch_related
        ))
        return method

    return decorator


def update_registry():
    """ add all additional info to REGISTRY. """
    from django.apps import apps
    global REGISTRY
    for (app_label, model_name), preload_infos in _REGISTRY.items():
        model = apps.get_model(app_label, model_name)
        REGISTRY[model] = model_info = ModelInfo(
            model=model,
            app_label=app_label,
            model_name=model_name,
        )
        for plinfo in preload_infos:
            method = getattr(model, plinfo.method_name)

            # read the description from the doc string
            docstring = inspect.getdoc(method)
            if docstring:
                description = docstring.split("\n\n")[0].rstrip()
            else:
                description = plinfo.method_name.replace("_", " ")

            model_info.validators[plinfo.method_name] = ValidatorInfo(
                model_info=model_info,
                method=method,
                method_name=plinfo.method_name,
                description=description[:MAX_DESCRIPTION_LEN],
                is_class_method=is_class_method(method, model),
                select_related=plinfo.select_related,
                prefetch_related=plinfo.prefetch_related,
            )

    # the temp registry is no longer needed
    _REGISTRY.clear()
