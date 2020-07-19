import inspect
from functools import lru_cache
from typing import Type

from django.db import models


class ConfigMeta(type):
    """ metaclass for configuration """
    CONFIG_OPTIONS = {
        "exclude",
    }

    def __new__(mcs, name, bases, attrs):
        cls = super().__new__(mcs, name, bases, attrs)
        own_attrs = set(a for a in attrs if not a.startswith("__"))
        diff = own_attrs - ConfigMeta.CONFIG_OPTIONS
        if len(diff) != 0:
            raise ValueError(
                f"{diff.pop()} is not a valid configuration option. "
                f"Optionals are: {', '.join(ConfigMeta.CONFIG_OPTIONS)}"
            )
        cls._owner_qualname = ".".join(attrs["__qualname__"].split(".")[:-1])
        return cls

    def __get__(cls, instance, owner):
        """ only return the class if was defined on owner """
        if cls._owner_qualname == owner.__qualname__:
            return cls
        return Config


class Config(metaclass=ConfigMeta):
    """ optional configuration specified on the model """

    # if True the model will not be included in the REGISTRY and will not
    # be processed during validation
    exclude = False


@lru_cache(maxsize=None)
def get_config(model: Type[models.Model]) -> Type[Config]:
    """ return the configuration on a model """
    for name, member in inspect.getmembers(model):
        if isinstance(member, type) and issubclass(member, Config):
            return member
    return Config
