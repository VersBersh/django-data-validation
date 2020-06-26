from dataclasses import dataclass, field
from typing import List, Optional, Union

from django.db.models import Model, QuerySet
from termcolor import colored


class Result:
    def __init__(self):
        self.comment = None
        self.allowed_to_fail = None


class _PASS(Result):
    def __call__(self):
        pass


class _FAIL(Result):
    def __call__(self,
                 comment: Optional[str] = None,
                 allowed_to_fail: Optional[bool] = None
                 ) -> "FAIL":
        self.comment = comment
        self.allowed_to_fail = allowed_to_fail
        return self


class _NA(Result):
    def __call__(self, comment: Optional[str] = None) -> "NA":
        self.comment = comment
        return self


PASS = _PASS()
FAIL = _FAIL()
NA = _NA()


@dataclass
class Summary:
    passed: Optional[bool] = None
    num_passed: Optional[int] = 0
    num_failed: Optional[int] = 0
    num_na: Optional[int] = 0
    failures: Union[QuerySet, List[Model], List[int]] = field(default_factory=list)
    _num_allowed_to_fail: Optional[int] = 0
    _exception_info: Optional[dict] = None

    def complete(self) -> "Summary":
        """ ensure that Summary is consistent and update the passed field """
        if self._exception_info is not None:
            self.passed = None
            self.num_passed = None
            self.num_failed = None
            self._num_allowed_to_fail = None
            self.failures = []
            return self

        attrs = ("num_passed", "num_failed", "num_na", "failures", "_num_allowed_to_fail")
        for attr in attrs:
            if getattr(self, attr) is None:
                raise AssertionError(f"Summary.{attr} is None")

        passed = max(self.num_failed, len(self.failures)) <= self._num_allowed_to_fail
        if self.passed is None:
            self.passed = passed
        elif self.passed != passed:
            raise AssertionError(
                "Summary.passed is inconsistent with Summary.num_failed and Summary.failures"
            )
        return self

    def status(self, colour: bool = True):
        if self.passed is True:
            return colored("PASSED", "green", attrs=["bold"]) if colour else "PASSED"
        elif self.passed is False:
            return colored("FAILING", "red", attrs=["bold"]) if colour else "FAILING"
        else:
            return colored("UNKNOWN", "grey", attrs=["bold"]) if colour else "UNKNOWN"

    def _pretty_print(self):
        if self._exception_info is None:
            if self.num_passed is not None:
                yield f"PASSED: {self.num_passed}"
            if self.num_failed is not None:
                yield f"FAILED: {self.num_failed}"
            if self.num_na is not None:
                yield f"NA: {self.num_na}"
            if self._num_allowed_to_fail is not None:
                yield f"Allowed to Fail: {self._num_allowed_to_fail}"
            if len(self.failures) != 0:
                ids = ", ".join(map(str, self.failures))
                if len(self.failures) == 3:
                    ids += "..."
                yield f"Failing Ids: {ids}"
        else:
            if "exc_obj_pk" in self._exception_info:
                obj_pk = f" (object pk={self._exception_info['exc_obj_pk']})"
            else:
                obj_pk = ""
            yield f"EXCEPTION: {self._exception_info['exc_type']}{obj_pk}"

    def pretty_print(self):
        return "\n".join(self._pretty_print())


