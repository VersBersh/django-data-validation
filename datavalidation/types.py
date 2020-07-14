from typing import Callable, List, NewType, Optional, Tuple, Type, Union

from django.db import models

from .results import Result, PASS, FAIL, NA, EXCEPTION, Summary


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

# the type for a data_validator
ValidatorType = NewType(
    "ValidatorType",
    Callable[[models.Model], Union[ResultType, SummaryType]]
)


def check_return_value(return_value: ResultType,
                       exception_info: Optional[dict] = None,
                       object_pk: Optional[int] = None,
                       ) -> Tuple[Type[Result], Optional[dict]]:
    """ check that the user has returned a valid ResultType

     :returns: the Status and exception info if there is any
    """
    if exception_info is not None:
        return EXCEPTION, exception_info
    elif return_value is PASS or isinstance(return_value, PASS) or return_value is True:
        return PASS, None
    elif return_value is FAIL or isinstance(return_value, FAIL) or return_value is False:
        return FAIL, None
    elif return_value is NA or isinstance(return_value, NA) or return_value is True:
        return NA, None
    else:
        return EXCEPTION, {
            "exc_type": "TypeError('data validators must return datavalidator.PASS, "
                        "datavalidator.FAIL, datavalidator.NA, True, or False')",
            "exc_obj_pk": object_pk,
        }
