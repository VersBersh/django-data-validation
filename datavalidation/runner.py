from datetime import datetime
import itertools
from typing import (
    Dict, Generator, Iterator, List, Optional, Tuple, Type
)

from django.db import models, transaction

from .models import (
    ExceptionInfoMixin, FailingObject, Validator
)
from .registry import REGISTRY, ValidatorInfo
from .results import (
    PASS, FAIL, NA, EXCEPTION,
    Result, ResultType, check_return_value,
    Status, SummaryEx,
)
from .utils import queryset_iterator, chunk

from .logging import logger


class ResultHandlerMixin:
    @staticmethod
    def handle_return_value(valinfo: ValidatorInfo,
                            obj: models.Model,
                            retval: ResultType,
                            exinfo: Optional[dict]
                            ) -> Tuple[Type[Result], Optional[dict], Optional[bool]]:
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
                extra_args["comment"] = exinfo["exc_type"]

            fobj, _ = FailingObject.objects.update_or_create(
                validator_id=valinfo.validator_id,
                content_type_id=valinfo.model_info.content_type_id,
                object_pk=obj.pk,
                defaults={"valid": True, **extra_args}
            )

            # if the object was (previously) marked as allowed to fail
            allowed_to_fail = fobj.allowed_to_fail

        return result, exinfo, allowed_to_fail

    @staticmethod
    def handle_summary(valinfo: ValidatorInfo,
                       summary: SummaryEx,
                       skip_failures: bool = False
                       ) -> SummaryEx:
        """ handle the Validation Summary

         :return: the completed Summary object
        """
        summary = summary.complete()
        extra_args = summary.exception_info.copy()
        if summary.status == Status.PASSING:
            extra_args["last_run_time"] = datetime.now()

        validator_id = valinfo.validator_id
        Validator.objects.filter(id=validator_id).update(
            status=summary.status,
            num_passing=summary.num_passing,
            num_na=summary.num_na,
            **extra_args,
        )

        # if failures were supplied then update the ValidationResult table
        if summary.failures is not None and not skip_failures:
            with transaction.atomic():
                for object_pks in chunk(summary.failures, 1000):
                    qs_update = FailingObject.objects.filter(
                        validator_id=validator_id,
                        object_pk__in=object_pks
                    ).select_for_update()
                    qs_update.update(valid=True, comment="")
                    pks_updated = qs_update.values_list("object_pk", flat=True)
                    objects_to_create = [
                        FailingObject(validator_id=validator_id,
                                      content_type_id=valinfo.model_info.content_type_id,
                                      object_pk=pk,
                                      comment="",
                                      valid=True)
                        for pk in set(object_pks) - set(pks_updated)
                    ]
                    FailingObject.objects.bulk_create(objects_to_create)

        return summary


class InstanceMethodRunner(ResultHandlerMixin):
    def __init__(self,
                 model: Type[models.Model],
                 validator_infos: List[ValidatorInfo]):
        super().__init__()
        self.model = model
        self.validator_infos = validator_infos
        assert all(not v.is_class_method for v in self.validator_infos)
        self._summaries = {info: SummaryEx() for info in self.validator_infos}
        self.summaries: Dict[ValidatorInfo, SummaryEx] = {}

    def run(self) -> Dict[ValidatorInfo, SummaryEx]:
        """ run all instance-method data validators against all objects

         :returns: a dictionary mapping ValidatorInfos to the SummaryEx
            containing the validation results
        """
        # mark failing objects from the previous run as invalid, but don't
        # delete them yet so we don't lose any with allowed_to_fail=True
        for valinfo in self.validator_infos:
            FailingObject.objects.filter(validator_id=valinfo.validator_id).update(valid=False)

        # iterate over each object in the table and call each data
        # validator on it. When an exception is encountered on a validator
        # remove it from the list
        valinfos = self.validator_infos.copy()
        for obj in self.iterate_model_objects():
            valinfos = list(self.run_for_object(valinfos, obj))

        # now we can delete the invalid objects
        for valinfo in self.validator_infos:
            qs = FailingObject.objects.filter(validator_id=valinfo.validator_id, valid=False)
            # noinspection PyProtectedMember
            qs._raw_delete(qs.db)

        for valinfo, summary in self._summaries.items():
            # skip_failures because we already created the FailingObjects
            # in the call to handle_result
            self.summaries[valinfo] = self.handle_summary(
                valinfo, summary, skip_failures=True
            )

        return self.summaries

    def run_for_object(self,
                       valinfos: List[ValidatorInfo],
                       obj: models.Model
                       ) -> Iterator[ValidatorInfo]:
        """ run each data validator on the given object

         :returns: the list of ValidatorInfos that did not hit an exception
        """
        for valinfo in valinfos:
            exinfo = self.run_validator_for_object(valinfo, obj)
            if exinfo is None:
                yield valinfo
            else:
                # stop calling this validator if an exception was hit
                self._summaries.pop(valinfo)
                exinfo["exc_obj_pk"] = obj.pk
                summary = SummaryEx(exception_info=exinfo)
                self.summaries[valinfo] = self.handle_summary(
                    valinfo, summary, skip_failures=True
                )

    def run_validator_for_object(self,
                                 valinfo: ValidatorInfo,
                                 obj: models.Model
                                 ) -> Optional[dict]:
        """ run the given data validator for a given object

         :returns: the exception info if there was any
        """
        # noinspection PyBroadException
        try:
            retval = valinfo.method(obj)
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
        return exinfo

    def iterate_model_objects(self, chunk_size: int = 2000) -> Generator[models.Model, None, None]:  # noqa E501
        """ iterate the objects of a model with select/prefetch related """
        select_related_lookups = set(itertools.chain(*[
            info.select_related for info in self.validator_infos
        ]))
        prefetch_related_lookups = set(itertools.chain(*[
            info.prefetch_related for info in self.validator_infos
        ]))
        queryset = self.model._meta.default_manager \
                       .select_related(*select_related_lookups) \
                       .prefetch_related(*prefetch_related_lookups)
        yield from queryset_iterator(queryset, chunk_size)


class ClassMethodRunner(ResultHandlerMixin):
    def __init__(self,
                 model: Type[models.Model],
                 validator_infos: List[ValidatorInfo]):
        super().__init__()
        self.model = model
        self.validator_infos = validator_infos
        assert all(v.is_class_method for v in self.validator_infos)
        self.summaries: Dict[ValidatorInfo, SummaryEx] = {}

    def run(self) -> Dict[ValidatorInfo, SummaryEx]:
        """ run all class-method validators

         :returns: a dictionary mapping ValidatorInfos to the SummaryEx
            containing the validation results
        """
        for valinfo in self.validator_infos:
            FailingObject.objects.filter(validator_id=valinfo.validator_id).update(valid=False)

        for valinfo in self.validator_infos:
            self.run_validator(valinfo)

        # clean up any remaining invalid FailingObjects
        for valinfo in self.validator_infos:
            qs = FailingObject.objects.filter(validator_id=valinfo.validator_id, valid=False)
            # noinspection PyProtectedMember
            qs._raw_delete(qs.db)

        return self.summaries

    def run_validator(self, valinfo: ValidatorInfo) -> None:
        """ run a given class-method validator and hande the result """
        # noinspection PyBroadException
        try:
            retval = valinfo.method()
            summary = SummaryEx.from_return_value(retval)
        except Exception:
            exinfo = ExceptionInfoMixin.get_exception_info()
            summary = SummaryEx(exception_info=exinfo)

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

    def run(self) -> List[Tuple[ValidatorInfo, SummaryEx]]:
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

        instance_summaries = InstanceMethodRunner(self.model, [
            self.model_info.validators[name]
            for name in self.method_names
            if not self.model_info.validators[name].is_class_method
        ]).run()
        summaries.update({k.method_name: (k, v) for k, v in instance_summaries.items()})

        class_summaries = ClassMethodRunner(self.model, [
            self.model_info.validators[name]
            for name in self.method_names
            if self.model_info.validators[name].is_class_method
        ]).run()
        summaries.update({k.method_name: (k, v) for k, v in class_summaries.items()})

        return [summaries[name] for name in self.method_names]


class ObjectValidationRunner(ResultHandlerMixin):
    """ validate a single object and update any FailingObjects """

    def __init__(self, obj: models.Model):
        self.obj = obj
        self.model = obj._meta.model
        self.model_info = REGISTRY[self.model]
        # only instance methods can be run for a single object
        self.validator_infos = [
            valinfo
            for valinfo in self.model_info.validators.values()
            if not valinfo.is_class_method
        ]

    def run(self) -> bool:
        """ run validation for specified object

         :returns: True if there was no validation erros
        """
        validator_ids = [v.validator_id for v in self.validator_infos]
        FailingObject.objects.filter(
            validator_id__in=validator_ids,
            object_pk=self.obj.pk
        ).update(valid=False)

        result = all([
            self.run_for_object(valinfo)
            for valinfo in self.validator_infos
        ])

        qs = FailingObject.objects.filter(
            validator_id__in=validator_ids,
            object_pk=self.obj.pk,
            valid=False
        )
        # noinspection PyProtectedMember
        qs._raw_delete(qs.db)

        return result

    def run_for_object(self, valinfo: ValidatorInfo) -> bool:
        """ run a validator for a single object

         :returns: True if there was no validation error
        """
        # noinspection PyBroadException
        try:
            retval = valinfo.method(self.obj)
            exinfo = None
        except Exception:
            retval = None
            exinfo = ExceptionInfoMixin.get_exception_info()

        result, exinfo, allowed_to_fail = self.handle_return_value(
            valinfo, self.obj, retval, exinfo
        )

        if result is PASS or result is NA:
            return True
        elif result is FAIL:
            return allowed_to_fail
        elif result is EXCEPTION:
            return False
        else:
            raise RuntimeError("that's.. impossible!")
