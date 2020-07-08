from datetime import datetime
import itertools
from typing import (
    Dict, Generator, Iterator, List, Optional, Tuple, Type, Union
)

from django.db import models
from termcolor import colored

from .models import (
    ExceptionInfoMixin, FailingObject, Validator
)
from .registry import REGISTRY, ValidatorInfo
from .results import PASS, FAIL, NA, Result, SummaryEx, Status
from .utils import queryset_iterator

from .logging import logger


class SummaryHandlerMixin:
    def __init__(self):
        self.summaries: Dict[ValidatorInfo, SummaryEx] = {}

    def handle_summary(self,
                       valinfo: ValidatorInfo,
                       summary: Optional[SummaryEx],
                       skip_failures: bool = False
                       ) -> None:
        """ handle the Validation Summary """
        vpk = valinfo.get_pk()
        extra_args = summary.exception_info
        if summary.status == Status.PASSING:
            extra_args["last_run_time"] = datetime.now()
        Validator.objects.filter(pk=vpk).update(
            status=summary.status,
            num_passing=summary.num_passing,
            num_failing=summary.num_failing,
            num_na=summary.num_na,
            **extra_args,
        )

        # if failures were supplied then update the ValidationResult table
        if summary.failures is not None and not skip_failures:
            for pk in summary.failures:
                FailingObject.objects.update_or_create(
                    validator_id=vpk,
                    object_pk=pk,
                    defaults={
                        "comment": "",
                        "valid": True,
                    }
                )
        self.summaries[valinfo] = summary
        return


class InstanceMethodRunner(SummaryHandlerMixin):
    def __init__(self,
                 model: Type[models.Model],
                 validator_infos: List[ValidatorInfo]):
        super().__init__()
        self.model = model
        self.validator_infos = validator_infos
        assert all(not v.is_class_method for v in self.validator_infos)
        self._summaries = {info: SummaryEx() for info in self.validator_infos}

    def run(self) -> Dict[ValidatorInfo, SummaryEx]:
        """ run all instance-method data validators against all objects

         :returns: a dictionary mapping ValidatorInfos to the SummaryEx
            containing the validation results
        """
        # delete failing objects from previous run, but retain objects
        # marked allowed_to_fail and set them as invalid so that field is
        # not lost
        for valinfo in self.validator_infos:
            qs = FailingObject.objects.filter(validator_id=valinfo.get_pk())
            # noinspection PyProtectedMember
            qs.exclude(allowed_to_fail=True)._raw_delete(qs.db)
            qs.update(valid=False)

        # iterate over each object in the table and call each data
        # validator on it. When an exception is encountered on a validator,
        # remove it from the list
        valinfos = self.validator_infos.copy()
        for obj in self.iterate_model_objects():
            valinfos = list(self.run_for_object(valinfos, obj))

        # clean up any remaining invalid FailingObjects
        for valinfo in self.validator_infos:
            qs = FailingObject.objects.filter(validator_id=valinfo.get_pk(), valid=False)
            # noinspection PyProtectedMember
            qs._raw_delete(qs.db)

        for valinfo, summary in self._summaries.items():
            # skip_failures because we already created the FailingObjects
            summary.complete()
            self.handle_summary(valinfo, summary, skip_failures=True)

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
                summary = SummaryEx(exception_info=exinfo).complete()
                self.handle_summary(valinfo, summary, skip_failures=True)

    def run_validator_for_object(self,
                                 valinfo: ValidatorInfo,
                                 obj: models.Model
                                 ) -> Optional[dict]:
        """ run the given data validator for a given object

         :returns: the exception info if there was any
        """
        # noinspection PyBroadException
        try:
            result = valinfo.method(obj)
            exinfo = None
        except Exception:
            result = None
            exinfo = ExceptionInfoMixin.get_exception_info()

        return self.handle_result(valinfo, obj, result, exinfo)

    def handle_result(self,
                      method_info: ValidatorInfo,
                      obj: models.Model,
                      result: Union[Result, bool, None],
                      exinfo: Optional[dict]
                      ) -> Optional[dict]:
        """ handle the result returned by an instance-method validator

         :returns: the exception info if there was any
        """
        summary = self._summaries[method_info]

        if result is PASS or isinstance(result, PASS) or result is True:
            summary.num_passing += 1

        elif result is FAIL or isinstance(result, FAIL) or result is False:
            summary.num_failing += 1

            # save the failing object
            extra_result_args = {}
            if isinstance(result, FAIL):
                if result.allowed_to_fail is not None:
                    extra_result_args["allowed_to_fail"] = result.allowed_to_fail
                    if result.comment:
                        extra_result_args["allowed_to_fail_justification"] = result.comment  # noqa E501
                elif result.comment:
                    extra_result_args["comment"] = result.comment

            fobj, _ = FailingObject.objects.update_or_create(
                validator_id=method_info.get_pk(),
                object_pk=obj.pk,
                defaults={
                    "valid": True,
                    **extra_result_args,
                }
            )
            summary.failures.append(obj.pk)

            # if the object was (previously) marked as allowed to fail then
            # update the current summary
            if fobj.allowed_to_fail:
                summary.num_allowed_to_fail += 1

        elif result is NA or isinstance(result, NA):
            summary.num_na += 1

        elif exinfo is None:
            exinfo = {
                "exc_type": "TypeError('data validators must return datavalidator.PASS, "
                            "datavalidator.FAIL, datavalidator.NA, True, or False')",
                "exc_obj_pk": obj.pk,
            }

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


class ClassMethodRunner(SummaryHandlerMixin):
    def __init__(self,
                 model: Type[models.Model],
                 validator_infos: List[ValidatorInfo]):
        super().__init__()
        self.model = model
        self.validator_infos = validator_infos
        assert all(v.is_class_method for v in self.validator_infos)

    def run(self) -> Dict[ValidatorInfo, SummaryEx]:
        """ run all class-method validators

         :returns: a dictionary mapping ValidatorInfos to the SummaryEx
            containing the validation results
        """
        for valinfo in self.validator_infos:
            qs = FailingObject.objects.filter(validator_id=valinfo.get_pk())
            # noinspection PyProtectedMember
            qs.exclude(allowed_to_fail=True)._raw_delete(qs.db)
            qs.update(valid=False)

        for valinfo in self.validator_infos:
            self.run_validator(valinfo)

        # clean up any remaining invalid FailingObjects
        for valinfo in self.validator_infos:
            qs = FailingObject.objects.filter(validator_id=valinfo.get_pk(), valid=False)
            # noinspection PyProtectedMember
            qs._raw_delete(qs.db)

        return self.summaries

    def run_validator(self, valinfo: ValidatorInfo) -> None:
        """ run a given class-method validator and hande the result """
        # noinspection PyBroadException
        try:
            returnval = valinfo.method()
            summary = SummaryEx.from_return_value(returnval)
        except Exception:
            exinfo = ExceptionInfoMixin.get_exception_info()
            summary = SummaryEx(exception_info=exinfo).complete()

        self.handle_summary(valinfo, summary)


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
            raise ValueError(f"no data_validation methods on model {model.__name__}")

    def check_method_names(self, method_names: List[str]) -> None:
        """ check that the list of method names are data validators """
        all_validators = self.model_info.validators.keys()
        for method in method_names:
            if method not in all_validators:
                raise ValueError(
                    f"{method} is not a data_validator on {self.model_info.model_name}"
                )

    def run(self) -> List[Tuple[ValidatorInfo, SummaryEx]]:
        """ run validation for specified method

         :returns: the list of ValidatorInfos and SummaryEx containing the
            validation summaries. If method_names was provided to __init__
            then the results are returned in the same order.
        """
        logger.info(colored(
            f"\nVALIDATING MODEL: {self.model_info!s}", "cyan", attrs=["bold"]
        ))
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
