from collections import Counter
from datetime import datetime
from typing import (
    Dict, Generator, List, Optional, Tuple, Type, Set, Any
)
try:
    from time import time_ns as timer
    TIME_UNIT = int(1e9)
except ImportError:
    from time import time as timer
    TIME_UNIT = 1

from django.core.exceptions import ObjectDoesNotExist, FieldError
from django.db import models, transaction
from tqdm import tqdm

from .models import (
    ExceptionInfoMixin, FailingObject, Validator  # noqa
)
from .registry import REGISTRY, ValidatorInfo
from .results import (
    check_return_value, PASS, FAIL, NA, EXCEPTION,
    ExceptionInfo, Result, Status, SummaryEx
)
from .utils import queryset_iterator, chunk, partition

from .logging import logger


__all__ = (
    "ModelValidationRunner",
    "ObjectValidationRunner",
)


class ResultHandlerMixin:
    @staticmethod
    def handle_return_value(valinfo: ValidatorInfo,
                            obj: models.Model,
                            retval: Any,
                            exinfo: Optional[ExceptionInfo]
                            ) -> Tuple[Type[Result], Optional[ExceptionInfo], Optional[bool]]:
        """ handle the value returned by an instance-method validator

         :returns: a tuple (result, exception_info, allowed_to_fail)
            result: return value of the method cast to Type[Result],
            exception_info: if there was an exception
            allowed_to_fail: set if result is FAIL and the object is marked
                allowed to fail
        """
        result, exinfo = check_return_value(retval, exinfo)
        allowed_to_fail: Optional[bool] = None

        if result is FAIL or result is EXCEPTION:
            # save the failing object
            extra_args = {}
            if isinstance(retval, FAIL):
                if retval.allowed_to_fail is not None:
                    extra_args["allowed_to_fail"] = retval.allowed_to_fail
                    if retval.comment:
                        extra_args["allowed_to_fail_justification"] = retval.comment
                elif retval.comment:
                    extra_args["comment"] = retval.comment
            elif result is EXCEPTION:
                extra_args["comment"] = exinfo.exc_type

            fobj, _ = FailingObject.all_objects.update_or_create(
                validator_id=valinfo.get_validator_id(),
                content_type_id=valinfo.model_info.get_content_type_id(),
                object_pk=obj.pk,
                defaults={
                    "is_valid": True,
                    "is_exception": result is EXCEPTION,
                    **extra_args
                }
            )

            # if the object was (previously) marked as allowed to fail
            allowed_to_fail = fobj.allowed_to_fail

        return result, exinfo, allowed_to_fail

    @staticmethod
    def update_failing_objects(valinfo: ValidatorInfo,
                               summary: SummaryEx
                               ) -> SummaryEx:
        """ add the failures to the FailingObject table """
        validator_id = valinfo.get_validator_id()
        summary.complete()
        if summary.failures is None:
            return summary

        with transaction.atomic():
            for object_pks in chunk(summary.failures, 1000):
                qs_update = FailingObject.all_objects.filter(
                    validator_id=validator_id,
                    object_pk__in=object_pks
                ).select_for_update()
                qs_update.update(is_valid=True, is_exception=False, comment="")
                pks_updated = qs_update.values_list("object_pk", flat=True)
                objects_to_create = [
                    FailingObject(validator_id=validator_id,
                                  content_type_id=valinfo.model_info.get_content_type_id(),
                                  object_pk=pk,
                                  is_exception=False,
                                  comment="",
                                  is_valid=True)
                    for pk in set(object_pks) - set(pks_updated)
                ]
                FailingObject.objects.bulk_create(objects_to_create)
        return summary

    @staticmethod
    def handle_summary(valinfo: ValidatorInfo,
                       summary: SummaryEx
                       ) -> SummaryEx:
        """ handle the Validation Summary

         :return: the completed Summary object
        """
        summary = summary.complete()
        extra_args = summary.exception_info_dict
        if summary.execution_time is not None:
            execution_time = summary.execution_time / TIME_UNIT
        else:
            execution_time = None

        Validator.objects.filter(id=valinfo.get_validator_id()).update(
            status=summary.status,
            num_passing=summary.num_passing,
            num_na=summary.num_na,
            last_run_time=datetime.now(),
            execution_time=execution_time,
            **extra_args,
        )

        return summary


class InstanceMethodRunner(ResultHandlerMixin):
    def __init__(self,
                 model: Type[models.Model],
                 validator_infos: List[ValidatorInfo]):
        self.model = model
        self.model_info = REGISTRY[model]
        self.validator_infos = validator_infos
        assert all(v.instance_method is not None for v in self.validator_infos)
        self._summaries = {info: SummaryEx() for info in self.validator_infos}
        self.summaries: Dict[ValidatorInfo, SummaryEx] = {}
        self._time = None

    def run(self, show_progress: bool) -> Dict[ValidatorInfo, SummaryEx]:
        """ run all instance-method data validators against all objects

         :returns: a dictionary mapping ValidatorInfos to the SummaryEx
            containing the validation results
        """
        # mark failing objects from the previous run as invalid, but don't
        # delete them yet so we don't lose any with allowed_to_fail=True
        for valinfo in self.validator_infos:
            FailingObject.all_objects.filter(
                validator_id=valinfo.get_validator_id()
            ).update(is_valid=False)

        # iterate over each object in the table and call each data
        # validator on it. When an exception is encountered on a validator
        # remove it from the list
        progress = tqdm if show_progress else lambda x: x
        valinfos = self.validator_infos.copy()
        for obj in progress(self.iterate_model_objects()):
            valinfos = list(self.run_for_object(valinfos, obj))

        # now we can delete the invalid objects
        for valinfo in self.validator_infos:
            qs = FailingObject.all_objects.filter(
                validator_id=valinfo.get_validator_id(), is_valid=False, allowed_to_fail=False
            )
            # noinspection PyProtectedMember
            qs._raw_delete(qs.db)

        for valinfo, summary in self._summaries.items():
            # skip_failures because we already created the FailingObjects
            # in the call to handle_result
            self.summaries[valinfo] = self.handle_summary(valinfo, summary)

        return self.summaries

    def run_for_object(self,
                       valinfos: List[ValidatorInfo],
                       obj: models.Model
                       ) -> Generator[ValidatorInfo, None, None]:
        """ run each data validator on the given object

         :returns: the list of ValidatorInfos that did not hit an exception
        """
        self._time = timer()
        for valinfo in valinfos:
            exinfo = self.run_validator_for_object(valinfo, obj)
            if exinfo is None:
                yield valinfo
            else:
                # stop calling this validator if an exception was hit
                self._summaries.pop(valinfo)
                exinfo.exc_obj_pk = obj.pk
                summary = SummaryEx.from_exception_info(exinfo)
                self.summaries[valinfo] = self.handle_summary(valinfo, summary)

    def run_validator_for_object(self,
                                 valinfo: ValidatorInfo,
                                 obj: models.Model
                                 ) -> Optional[ExceptionInfo]:
        """ run the given data validator for a given object

         :returns: the exception info if there was any
        """
        # noinspection PyBroadException
        try:
            retval = valinfo.instance_method(obj)
            exinfo = None
        except Exception:
            retval = None
            exinfo = ExceptionInfoMixin.get_exception_info()

        result, exinfo, allowed_to_fail = self.handle_return_value(
            valinfo, obj, retval, exinfo
        )

        summary = self._summaries[valinfo]
        if result is PASS:
            summary.num_passing += 1
        elif result is FAIL:
            summary.failures.append(obj.pk)
            if allowed_to_fail:
                summary.num_allowed_to_fail += 1
        elif result is NA:
            summary.num_na += 1

        t = timer()
        execution_time, self._time = t - self._time, t
        if summary.execution_time is not None:
            summary.execution_time += execution_time

        return exinfo

    def get_related_lookups(self) -> Tuple[Set[str], Set[str]]:
        """ check that the select_related and prefetch_related fields are
            valid and display a warning if they are not

         :returns: the union of valid select related and prefetch related
            fields accross all validators on the model
        """
        qs = self.model._meta.default_manager.all()

        try:
            obj = qs.first()
        except ObjectDoesNotExist:
            return set(), set()

        select_related = set()
        for valinfo in self.validator_infos:
            not_seen = valinfo.select_related - select_related
            if len(not_seen) != 0:
                try:
                    qs.select_related(*not_seen).first()
                    select_related |= not_seen
                except FieldError as e:
                    logger.cwarning(
                        f"{e.args[0]}. select_related fields will be skipped for"
                        f" {self.model_info.model_name}.{valinfo.method_name}"
                    )

        prefetch_related = set()
        for valinfo in self.validator_infos:
            not_seen = valinfo.prefetch_related - prefetch_related
            if len(not_seen) != 0:
                try:
                    models.prefetch_related_objects([obj], *valinfo.prefetch_related)
                    prefetch_related |= not_seen
                except (FieldError, AttributeError, ValueError) as e:
                    logger.cwarning(
                        f"{e.args[0]}. prefetch_realted will be skipped for "
                        f"{self.model_info.model_name}.{valinfo.method_name}"
                    )

        return select_related, prefetch_related

    def iterate_model_objects(self, chunk_size: int = 2000) -> Generator[models.Model, None, None]:  # noqa E501
        """ iterate the objects of a model with select/prefetch related """
        select_related, prefetch_related = self.get_related_lookups()
        queryset = self.model._meta.default_manager \
                       .select_related(*select_related) \
                       .prefetch_related(*prefetch_related)
        yield from queryset_iterator(queryset, chunk_size)


class ClassMethodRunner(ResultHandlerMixin):
    def __init__(self,
                 model: Type[models.Model],
                 validator_infos: List[ValidatorInfo]):
        super().__init__()
        self.model = model
        self.validator_infos = validator_infos
        assert all(v.class_method is not None for v in self.validator_infos)
        self.summaries: Dict[ValidatorInfo, SummaryEx] = {}

    def run(self) -> Dict[ValidatorInfo, SummaryEx]:
        """ run all class-method validators

         :returns: a dictionary mapping ValidatorInfos to the SummaryEx
            containing the validation results
        """
        for valinfo in self.validator_infos:
            FailingObject.all_objects.filter(
                validator_id=valinfo.get_validator_id()
            ).update(is_valid=False)

        for valinfo in self.validator_infos:
            self.run_validator(valinfo)

        # clean up any remaining invalid FailingObjects
        for valinfo in self.validator_infos:
            qs = FailingObject.all_objects.filter(
                validator_id=valinfo.get_validator_id(), is_valid=False, allowed_to_fail=False
            )
            # noinspection PyProtectedMember
            qs._raw_delete(qs.db)

        return self.summaries

    def run_validator(self, valinfo: ValidatorInfo) -> None:
        """ run a given class-method validator and hande the result """
        # noinspection PyBroadException
        t0 = timer()
        try:
            retval = valinfo.class_method(self.model)
            summary = SummaryEx.from_return_value(retval)
        except Exception:  # noqa
            exinfo = ExceptionInfoMixin.get_exception_info()
            summary = SummaryEx.from_exception_info(exinfo)

        summary = self.update_failing_objects(valinfo, summary)
        summary.execution_time = timer() - t0
        self.summaries[valinfo] = self.handle_summary(valinfo, summary)


class ModelValidationRunner:
    """ validate a model and update the results table """

    def __init__(self,
                 model: Type[models.Model],
                 method_names: Optional[List[str]] = None):
        self.check_model(model)
        self.model = model
        self.model_info = REGISTRY[model]
        self.method_names = method_names
        if method_names is None:
            self.method_names = self.model_info.validators.keys()  # all validators
        else:
            self.check_method_names(method_names)
        self.validated = False

    @staticmethod
    def check_model(model: Type[models.Model]) -> None:
        if model not in REGISTRY:
            raise ValueError(f"no data validation methods on model {model.__name__}")

    def check_method_names(self, method_names: List[str]) -> None:
        """ check that the list of method names are data validators """
        all_validators = self.model_info.validators.keys()
        for method in method_names:
            if method not in all_validators:
                raise ValueError(
                    f"{method} is not a data validator on {self.model_info.model_name}"
                )

    def run(self, show_progress: bool = False) -> List[Tuple[ValidatorInfo, SummaryEx]]:
        """ run validation for specified method

         :returns: the list of ValidatorInfos and SummaryEx containing the
            validation summaries. If method_names was provided to __init__
            then the results are returned in the same order.
        """
        logger.cinfo(f"\nVALIDATING MODEL: {self.model_info!s}")
        if self.validated:
            raise Exception("can only call validate once per instance.")
        else:
            self.validated = True

        summaries: Dict[str, Tuple[ValidatorInfo, SummaryEx]] = {}

        classmethod_infos, instancemethod_infos = partition(
            (self.model_info.validators[name] for name in self.method_names),
            predicate=lambda valinfo: valinfo.class_method is not None
        )

        class_summaries = ClassMethodRunner(self.model, classmethod_infos).run()
        summaries.update({k.method_name: (k, v) for k, v in class_summaries.items()})

        instance_summaries = InstanceMethodRunner(self.model, instancemethod_infos).run(show_progress)  # noqa E501
        summaries.update({k.method_name: (k, v) for k, v in instance_summaries.items()})

        return [summaries[name] for name in self.method_names]


class ObjectValidationRunner(ResultHandlerMixin):
    """ validate a single object and update any FailingObjects """

    def __init__(self, obj: models.Model):
        self.obj = obj
        self.model = obj._meta.model
        self.model_info = REGISTRY[self.model]
        # note the distinction with ModelValidationRunner, to run a single
        # object the instance methods take precedence over class methods.
        # this is the whole point of overloading data validators.
        self.instancemethod_infos, self.classmethod_infos = partition(
            self.model_info.validators.values(),
            predicate=lambda valinfo: valinfo.instance_method is not None
        )

    def run(self, class_methods: bool = True) -> Tuple[int, int, int]:
        """ run validation for specified object

         Args:
            class_methods: if True then also re-run the (non-overloaded)
                class methods on the model.

         :returns: a tuple of the number passing (or na), the number
            failing, and the number of exceptions
        """
        validator_ids = [v.get_validator_id() for v in self.instancemethod_infos]
        FailingObject.all_objects.filter(
            validator_id__in=validator_ids, object_pk=self.obj.pk
        ).update(is_valid=False)

        instance_results = [
            self.run_for_object(valinfo)
            for valinfo in self.instancemethod_infos
        ]

        qs = FailingObject.all_objects.filter(
            validator_id__in=validator_ids,
            object_pk=self.obj.pk,
            is_valid=False,
            allowed_to_fail=False
        )
        # noinspection PyProtectedMember
        qs._raw_delete(qs.db)

        if class_methods:
            class_results = ClassMethodRunner(self.model, self.classmethod_infos).run()
        else:
            class_results = {}

        results = Counter()
        for result in instance_results:
            results[result] += 1
        for summary in class_results.values():
            results[summary.status] += 1

        keys = (Status.PASSING, Status.FAILING, Status.EXCEPTION)
        assert set(results.keys()) <= set(keys), f"unknown status {results.keys()!s}"
        return tuple(results[key] for key in keys)  # noqa

    def run_for_object(self, valinfo: ValidatorInfo) -> Status:
        """ run a validator for a single object

         :returns: True if there was no validation error
        """
        # noinspection PyBroadException
        try:
            retval = valinfo.instance_method(self.obj)
            exinfo = None
        except Exception:
            retval = None
            exinfo = ExceptionInfoMixin.get_exception_info()

        result, exinfo, allowed_to_fail = self.handle_return_value(
            valinfo, self.obj, retval, exinfo
        )

        self.update_validator(valinfo, result, exinfo)

        if result is PASS or result is NA or (result is FAIL and allowed_to_fail):
            return Status.PASSING
        elif result is FAIL:
            return Status.FAILING
        elif result is EXCEPTION:
            return Status.EXCEPTION
        else:
            raise RuntimeError("that's.. impossible!")

    @staticmethod
    @transaction.atomic
    def update_validator(valinfo: ValidatorInfo,
                         result: Type[Result],
                         exinfo: Optional[ExceptionInfo]
                         ) -> None:
        # running validation for one object may change the status of the
        # entire Validator (e.g. if this object was the only one failing)
        validator = Validator.objects.select_for_update().get(id=valinfo.get_validator_id())
        if validator.status == Status.EXCEPTION:
            return  # don't update
        elif result is EXCEPTION:
            validator.status = Status.EXCEPTION
            validator.__dict__.update(exinfo.__dict__)
            validator.save()
            return

        failures = validator.failing_objects.filter(is_valid=True, allowed_to_fail=False)

        # edge case: the validator is overloaded, the class method only
        # returns a bool (i.e. it doesn't return the objects that failed),
        # and the validator is Failing. Then we cannot make any inference
        # about how this single object impacts the validator.
        is_edge_case = (
                valinfo.instance_method is not None and
                valinfo.class_method is not None and
                failures.count() == 0 and
                validator.status == Status.FAILING
        )
        if is_edge_case:
            return  # cannot do anything

        new_status = Status.PASSING if failures.count() == 0 else Status.FAILING
        if validator.status != new_status:
            validator.status = new_status
            validator.save()
