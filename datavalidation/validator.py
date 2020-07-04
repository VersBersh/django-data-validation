from datetime import datetime
import itertools
from typing import List, Optional, Type, Iterator, Any

from django.db import models
from termcolor import colored

from .models import (
    ExceptionInfoMixin, FailingObject, Validator
)
from .registry import REGISTRY, ValidatorInfo
from .results import PASS, FAIL, NA, Result, SummaryEx, Status
from .utils import queryset_iterator

from .logging import logger


# noinspection PyProtectedMember
class ModelValidator:
    """ validate a model and update the results table """

    def __init__(self,
                 model: Type[models.Model],
                 method_names: Optional[List[str]] = None):
        if model not in REGISTRY:
            raise ValueError(f"no data_validation methods on model {model.__name__}")

        self.model = model
        self.model_info = REGISTRY[model]

        if method_names is None:
            method_names = self.model_info.validators.keys()  # all validators
        else:
            self._check_method_names(method_names)

        self.class_validator_infos = [
            self.model_info.validators[name]
            for name in method_names
            if self.model_info.validators[name].is_class_method
        ]
        self.instance_validator_infos = [
            self.model_info.validators[name]
            for name in method_names
            if not self.model_info.validators[name].is_class_method
        ]
        self.instance_summaries = {
            info: SummaryEx() for info in self.instance_validator_infos
        }
        self.all_summaries = []
        self.validated = False

    def validate(self):
        """ run validation for specified method """
        logger.info(colored(
            f"running validation for model: {self.model_info!s}",
            "cyan", attrs=["bold"]
        ))
        if self.validated:
            raise Exception("can only call validate once per instance.")
        else:
            self.validated = True
        self._run_instance_validators()
        self._run_class_validators()
        self._print_summaries()

    def _check_method_names(self, method_names: List[str]):
        """ check that the list of method names are data validators """
        all_validators = self.model_info.validators.keys()
        for method in method_names:
            if method not in all_validators:
                raise ValueError(
                    f"{method} is not a data_validator on {self.model_info.model_name}"
                )

    def _run_instance_validators(self):
        """ run all instance-method data validators """
        # delete failing objects from previous run, but retain objects
        # marked allowed_to_fail and set them as invalid so that field is
        # not lost
        for valinfo in itertools.chain(self.instance_validator_infos,
                                       self.class_validator_infos):
            qs = FailingObject.objects.filter(validator_id=valinfo.get_pk())
            qs.exclude(allowed_to_fail=True).delete()
            qs.update(valid=False)

        # iterate over each object in the table and call each data
        # validator on it. When an exception is encountered on a validator,
        # remove it from the list
        valinfos = self.instance_validator_infos.copy()
        for obj in self.iterate_model_objects():
            valinfos = list(
                self._run_instance_validator_for_obj(valinfos, obj)
            )

        # clean up any remaining invalid FailingObjects
        for valinfo in itertools.chain(self.instance_validator_infos,
                                       self.class_validator_infos):
            FailingObject.objects.filter(
                validator_id=valinfo.get_pk(), valid=False
            ).delete()

        for valinfo, summary in self.instance_summaries.items():
            # skip_failures because we already created the FailingObjects
            summary.complete()
            self._handle_summary(valinfo, summary, skip_failures=True)

    def _run_instance_validator_for_obj(self,
                                        valinfos: List[ValidatorInfo],
                                        obj: models.Model
                                        ) -> Iterator[ValidatorInfo]:
        """ run the each data validator on the object """
        for valinfo in valinfos:
            exinfo = self._validate_instance(valinfo, obj)
            if exinfo is None:
                yield valinfo
            else:
                # stop calling this validator if an exception was hit
                self.instance_summaries.pop(valinfo)
                exinfo["exc_obj_pk"] = obj.pk
                summary = SummaryEx(exception_info=exinfo).complete()
                self._handle_summary(valinfo, summary, skip_failures=True)

    def _validate_instance(self,
                           valinfo: ValidatorInfo,
                           obj: models.Model
                           ) -> Optional[dict]:
        """ call the data validator for a given object

         returns: the exception info if there was any
        """
        # noinspection PyBroadException
        try:
            result = valinfo.method(obj)
            exinfo = None
        except Exception:
            result = None
            exinfo = ExceptionInfoMixin.get_exception_info()

        return self._handle_result(valinfo, obj, result, exinfo)

    def _run_class_validators(self):
        """ run all class-method validators """
        for valinfo in self.class_validator_infos:
            self._run_class_validator(valinfo)

    def _run_class_validator(self, valinfo: ValidatorInfo):
        # noinspection PyBroadException
        try:
            returnval = valinfo.method()
            summary = SummaryEx.from_return_value(returnval)
        except Exception:
            exinfo = ExceptionInfoMixin.get_exception_info()
            summary = SummaryEx(exception_info=exinfo).complete()

        try:
            summary.complete()
        except AssertionError:
            exinfo = ExceptionInfoMixin.get_exception_info()
            summary = SummaryEx(exception_info=exinfo).complete()

        self._handle_summary(valinfo, summary)

    def _handle_result(self,
                       method_info: ValidatorInfo,
                       obj: models.Model,
                       result: Optional[Result],
                       exinfo: Optional[dict]
                       ) -> Optional[dict]:
        """ handle the result returned by an instance-method validator """
        summary = self.instance_summaries[method_info]

        if result is PASS or isinstance(result, PASS):
            summary.num_passing += 1
        elif result is NA or isinstance(result, NA):
            summary.num_na += 1
        elif result is FAIL or isinstance(result, FAIL):
            summary.num_failing += 1

            # save the failing object
            extra_result_args = {}

            if result.allowed_to_fail is not None:
                extra_result_args["allowed_to_fail"] = result.allowed_to_fail
                if result.comment:
                    extra_result_args["allowed_to_fail_justification"] = result.comment
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
            summary.failures.append(fobj.pk)

            # if the object was (previously) marked as allowed to fail then
            # update the current summary
            if fobj.allowed_to_fail:
                summary.num_allowed_to_fail += 1

        elif exinfo is None:
            exinfo = {
                "exc_type": "TypeError('data validators must return datavalidator.PASS, "
                            "datavalidator.FAIL, or datavalidator.NA')",
                "exc_obj_pk": obj.pk,
            }

        return exinfo

    def _handle_summary(self,
                        valinfo: ValidatorInfo,
                        summary: Optional[SummaryEx],
                        skip_failures: bool = False
                        ) -> SummaryEx:
        """ handle the summary returned by a class-method validator """
        vpk = valinfo.get_pk()
        exinfo = summary.exception_info or {}
        if summary.status == Status.EXCEPTION:
            exinfo["last_run_time"] = datetime.now()
        Validator.objects.filter(pk=vpk).update(
            status=summary.status,
            num_passing=summary.num_passing,
            num_failing=summary.num_failing,
            num_na=summary.num_na,
            **exinfo,
        )

        # if failures were supplied then update the ValidationResult table
        if summary.failures is not None and not skip_failures:
            for pk in summary.failures:
                FailingObject.objects.update_or_create(
                    validator_id=vpk,
                    object_pk=pk,
                    defaults={
                        "comment": "",
                    }
                )
        self.all_summaries.append((valinfo, summary))
        return summary

    def iterate_model_objects(self, chunk_size: int = 2000) -> Iterator[Any]:
        select_related_lookups = set(itertools.chain(*[
            info.select_related for info in self.instance_validator_infos
        ]))
        prefetch_related_lookups = set(itertools.chain(*[
            info.prefetch_related for info in self.instance_validator_infos
        ]))
        queryset = self.model._meta.default_manager \
                       .select_related(*select_related_lookups) \
                       .prefetch_related(*prefetch_related_lookups)
        yield from queryset_iterator(queryset, chunk_size)

    def _print_summaries(self):
        for valinfo, summary in self.all_summaries:
            logger.info(
                f"\nMETHOD: {valinfo.method_name}: {summary.print_status()}\n"
                f"'''{valinfo.description}'''\n"
                f"{summary.pretty_print()}\n"
                f"-------------------------"
            )
