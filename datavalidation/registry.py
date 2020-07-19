import inspect
from functools import lru_cache
from typing import (
    Callable, Dict, Optional, Sequence, Type, Union, Set,
)

from dataclasses import dataclass, field
from django.db import models

from .constants import MAX_DESCRIPTION_LEN
from .types import ValidatorType
from .utils import is_class_method


@dataclass
class DecoratorArgs:
    """ arguments passed to the data_validator decorator """
    select_related: Set[str] = field(default_factory=tuple)
    prefetch_related: Set[str] = field(default_factory=tuple)


@dataclass
class ValidatorInfo:
    """ information about a data validator. """
    model_info: "ModelInfo"
    method: Callable
    method_name: str
    description: str
    is_class_method: bool
    select_related: set
    prefetch_related: set

    def __str__(self):
        mi = self.model_info
        return f"{mi.app_label}.{mi.model_name}.{self.method_name}"

    def __hash__(self):
        return hash(str(self))

    @lru_cache(maxsize=None)
    def get_validator_id(self) -> int:
        """ return the primary key of the corresponding ValidationMethod """
        from .models import Validator
        obj, _ = Validator.objects.update_or_create(
            app_label=self.model_info.app_label,
            model_name=self.model_info.model_name,
            method_name=self.method_name,
            defaults={
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

    @lru_cache(maxsize=None)
    def get_content_type_id(self) -> int:
        from django.contrib.contenttypes.models import ContentType
        return ContentType.objects.get_for_model(self.model).id


class Registry(dict):
    """ the registry of models and their validators """
    def __init__(self):
        super().__init__()
        self.synced = False

    def sync_to_db(self):
        """ ensure a record for each validator exists in the database """
        if self.synced:
            return
        for model_info in self.values():
            for valinfo in model_info.validators.values():
                valinfo.get_validator_id()
        self.synced = True


REGISTRY = Registry()


def data_validator(_method: Optional[ValidatorType] = None,
                   *,
                   select_related: Union[Sequence, str, None] = None,
                   prefetch_related: Union[Sequence, str, None] = None,
                   ) -> ValidatorType:
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
                    ) -> ValidatorType:
    """ add decorator arguments to the data validator """
    if select_related is None:
        select_related = set()
    elif isinstance(select_related, str):
        select_related = {select_related}
    else:
        select_related = set(select_related)

    if prefetch_related is None:
        prefetch_related = set()
    elif isinstance(prefetch_related, str):
        prefetch_related = {prefetch_related}
    else:
        prefetch_related = set(prefetch_related)

    def decorator(method: ValidatorType) -> ValidatorType:
        qualname = getattr(method, "__qualname__", "")
        # hack: methods defined on classes have "." in their qualified name,
        # and methods defined within other functions have "<locals>"
        if "." not in qualname or "<locals>" in qualname:
            raise ValueError("data validators must be methods of a class")
        # nb. we cannot determine anything else until the apps are loaded
        method._datavalidation_decorator_args = DecoratorArgs(
            select_related=select_related,
            prefetch_related=prefetch_related
        )
        return method

    return decorator


def update_registry():
    """ add all additional info to REGISTRY. """
    from django.apps import apps
    global REGISTRY

    for model in apps.get_models():
        validators = inspect.getmembers(
            model, predicate=lambda m: hasattr(m, "_datavalidation_decorator_args")
        )
        if len(validators) == 0:
            continue
        app_label = model._meta.app_label  # noqa
        model_name = model.__name__  # noqa
        REGISTRY[model] = model_info = ModelInfo(
            model=model,
            app_label=app_label,
            model_name=model_name,
        )
        for method_name, validator in validators:
            args = validator._datavalidation_decorator_args  # noqa

            # read the description from the doc string
            docstring = inspect.getdoc(validator)
            if docstring:
                description = docstring.split("\n\n")[0].strip()
            else:
                description = method_name.replace("_", " ")

            model_info.validators[method_name] = ValidatorInfo(
                model_info=model_info,
                method=validator,
                method_name=method_name,
                description=description[:MAX_DESCRIPTION_LEN],
                is_class_method=is_class_method(validator, model),
                select_related=args.select_related,
                prefetch_related=args.prefetch_related,
            )
