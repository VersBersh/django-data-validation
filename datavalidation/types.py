from typing import Callable, List, NewType, Type, Union

from django.db import models

from .results import Result, PASS, FAIL, Summary


# the return type of an instance method data_validator
ResultType = NewType("ResultType", Union[bool, Result, Type[Result]])

# the return type of a class method data_validator
SummaryType = NewType(
    "SummaryType",
    Union[
        Summary,
        bool, PASS, FAIL, Type[PASS], Type[FAIL],
        List[int], List[models.Model], models.QuerySet
    ]
)

# the type for an instance method validator
InstanceValidatorType = NewType(
    "InstanceValidatorType",
    Callable[[models.Model], ResultType]
)

# the type for a class method validator
ClassValidatorType = NewType(
    "ClassValidatorType",
    Callable[[models.Model], SummaryType]
)

# the type for a generic validator method
ValidatorType = NewType(
    "ValidatorType",
    Union[InstanceValidatorType, ClassValidatorType]
)
