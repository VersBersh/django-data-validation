from dataclasses import dataclass, field
import enum
from typing import List, Optional, Union, Any, NewType, Type, Generator

from django.db.models import Model, QuerySet
from termcolor import colored as coloured


class Status(enum.Enum):
    UNINITIALIZED = 0
    PASSING = 1
    FAILING = 2
    EXCEPTION = 3
    WARNING = 4

    @property
    def colour(self) -> str:
        if self == Status.UNINITIALIZED:
            return "white"
        if self == Status.PASSING:
            return "green"
        elif self == Status.FAILING:
            return "red"
        elif self == Status.EXCEPTION:
            return "grey"
        elif self == Status.WARNING:
            return "yellow"


@dataclass
class Result:
    comment: Optional[str] = None
    allowed_to_fail: Optional[bool] = None


class PASS(Result):
    pass


class FAIL(Result):
    pass


class NA(Result):
    pass


ResultType = NewType("ResultType", Union[bool, Result, Type[Result]])


@dataclass
class Summary:
    num_passing: Optional[int] = 0
    num_failing: Optional[int] = 0
    num_na: Optional[int] = 0
    failures: Union[QuerySet, List[Model], List[int]] = field(default_factory=list)


# internal use only
@dataclass
class SummaryEx(Summary):
    """ Summary Extended (keep some methods away from the user) """
    status: Optional[Status] = Status.UNINITIALIZED
    num_allowed_to_fail: Optional[int] = 0
    exception_info: Optional[dict] = None

    def __eq__(self, other: "SummaryEx") -> bool:
        # only used during testing
        for prop, val in self.__dict__.items():
            if prop == "failures":
                if sorted(list(val)) != sorted(list(other.failures)):
                    return False
            elif prop == "exception_info":
                if type(val) is not type(other.exception_info):  # noqa E721
                    return False
                if val is not None:
                    if sorted(val.items()) != sorted(other.exception_info.items()):
                        return False
            elif val != getattr(other, prop):
                return False
        else:
            return True

    @classmethod
    def from_summary(cls, summary: Summary) -> "SummaryEx":
        for attr in ("num_passing", "num_failing", "num_na"):
            if not type(getattr(summary, attr)) is int:
                raise TypeError(f"Summary.{attr} must be an int")
        if not isinstance(summary.failures, (QuerySet, list)):
            raise TypeError("Summary.failures must be a QuerySet, or list")
        summary_ex = cls()
        summary_ex.__dict__.update(summary.__dict__)
        return summary_ex.complete()

    @classmethod
    def from_return_value(cls, returnval: Any) -> "SummaryEx":
        """ convert the return value from a classmethod validator to a
            SummaryEx

         class methods may return:
            - PASS or FAIL,
            - True or False, or
            - a QuerySet, list of objects or list of primary keys that
              represent the objects that are failing the test
            - an instance of Summary
        """
        if isinstance(returnval, Summary):
            return cls.from_summary(returnval)
        elif returnval is True or returnval is PASS or isinstance(returnval, PASS):
            return SummaryEx(status=Status.PASSING, num_passing=None,
                             num_failing=None, num_na=None,
                             num_allowed_to_fail=None).complete()
        elif returnval is False or returnval is FAIL or isinstance(returnval, FAIL):
            return SummaryEx(status=Status.FAILING, num_passing=None,
                             num_failing=None, num_na=None,
                             num_allowed_to_fail=None).complete()
        elif isinstance(returnval, (QuerySet, list)):
            return SummaryEx(failures=returnval, num_passing=None,
                             num_failing=None, num_na=None,
                             num_allowed_to_fail=None).complete()
        else:
            raise TypeError(
                f"{type(returnval)} is not a permissible return value for "
                f"a classmethod validator. Permissible types are: "
                f"datavalidator.Summary, True, False, datavalidator.PASS, "
                f"datavalidator.FAIL, django.db.models.QuerySet, a list "
                f"(of objects or object ids)"
            )

    def complete(self) -> "SummaryEx":
        """ ensure that Summary is consistent and update self.passed """
        exinfo = {
            "exc_type": None,
            "exc_traceback": None,
            "exc_obj_pk": None,
        }
        attrs = ("num_passing", "num_failing", "num_na", "num_allowed_to_fail")
        if self.is_exception:
            exinfo.update(self.exception_info)
            self.exception_info = exinfo
            self.status = Status.EXCEPTION
            for attr in attrs:
                setattr(self, attr, None)
            self.failures = []
            return self
        else:
            self.exception_info = exinfo

        self.failures = self.get_failure_pks()
        if self.num_failing is not None and len(self.failures) != self.num_failing:
            raise AssertionError("Summary.num_failing != len(Summary.failures)")

        nones = [attr for attr in attrs if getattr(self, attr) is None]
        if len(nones) == 4:
            if self.status == Status.UNINITIALIZED:
                self.status = Status.PASSING if len(self.failures) == 0 else Status.FAILING

        elif len(nones) == 0:
            if self.num_failing <= self.num_allowed_to_fail:  # noqa
                status = Status.PASSING
            else:
                status = Status.FAILING

            if self.status == Status.UNINITIALIZED:
                self.status = status
            elif self.status != status:
                raise ValueError("inconsistent SummaryEx")

        else:
            raise TypeError(f"Summary.{nones[0]} is None")

        return self

    def get_failure_pks(self) -> List[int]:
        """ convert self.faliures to a list of primary keys """
        error_message = (
            "Summary.failures expects a QuerySet, a list of objects, or a "
            "list of primary keys"
        )
        if isinstance(self.failures, QuerySet):
            return list(self.failures.values_list("pk", flat=True))
        elif isinstance(self.failures, list):
            if len(self.failures) == 0:
                return self.failures
            elif isinstance(self.failures[0], Model):
                try:
                    return [obj.pk for obj in self.failures]
                except AttributeError:
                    raise TypeError(error_message)
            else:
                if not all(isinstance(el, int) for el in self.failures):
                    raise TypeError(error_message)
                return self.failures
        else:
            raise TypeError(error_message)

    @property
    def is_exception(self) -> bool:
        if self.exception_info is None:
            return False
        return self.exception_info["exc_type"] is not None

    def print_status(self, colour: bool = True) -> str:
        if not colour:
            return self.status.name
        return coloured(self.status.name, self.status.colour, attrs=["bold"])

    def _pretty_print(self) -> Generator[str, None, None]:
        if not self.is_exception:
            if self.num_passing is not None:
                yield f"PASSED: {self.num_passing}"
            if self.num_failing is not None:
                yield f"FAILED: {self.num_failing}"
            if self.num_na is not None:
                yield f"NA: {self.num_na}"
            if self.num_allowed_to_fail is not None:
                yield f"Allowed to Fail: {self.num_allowed_to_fail}"
            if len(self.failures) != 0:
                ids = ", ".join(map(str, self.failures[:3]))
                if len(self.failures) > 3:
                    ids += "..."
                yield f"Failing Ids: {ids}"
        else:
            if "exc_obj_pk" in self.exception_info:
                obj_pk = f" (object pk={self.exception_info['exc_obj_pk']})"
            else:
                obj_pk = ""
            yield f"EXCEPTION: {self.exception_info['exc_type']}{obj_pk}"

    def pretty_print(self) -> str:
        return "\n".join(self._pretty_print())
