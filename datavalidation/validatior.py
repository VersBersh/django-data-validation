import inspect
import itertools
from typing import List, Optional, Type, Iterator, Any, Union

from django.db import models
from termcolor import colored

from .models import (
    ExceptionInfoMixin, FailingObjects, ValidationSummary
)
from .registry import REGISTRY, MethodInfo
from .results import PASS, FAIL, Result, Summary
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
            method_names = self.model_info.methods.keys()  # all validators
        else:
            self._check_method_names(method_names)

        self.classmethodinfos = [
            self.model_info.methods[name]
            for name in method_names
            if self.model_info.methods[name].is_class_method
        ]
        self.instancemethodinfos = [
            self.model_info.methods[name]
            for name in method_names
            if not self.model_info.methods[name].is_class_method
        ]
        self.instance_summaries = {
            info: Summary() for info in self.instancemethodinfos
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
        self._validate_instancemethods()
        self._validate_classmethods()
        self._print_summaries()

    def _check_method_names(self, method_names: List[str]):
        """ check that the list of method names exist in the model """
        methods = {
            method.__name__
            for method in inspect.getmembers(self.model, predicate=inspect.ismethod)
        }
        for method in method_names:
            if method not in methods:
                raise ValueError(f"no method {method} on {self.model_info.model_name}")

    def _validate_instancemethods(self):
        """ run all instance-method data validators """
        # delete failing objects from previous run, but retain objects
        # marked allowed_to_fail and set them as invalid so that field is
        # not lost
        for method_info in itertools.chain(self.instancemethodinfos, self.classmethodinfos):
            qs = FailingObjects.objects.filter(
                content_type_id=self.model_info.content_type_id(),
                method_id=method_info.get_pk()
            )
            qs.exclude(allowed_to_fail=True).delete()
            qs.update(valid=False)

        # iterate over each object in the table and call each data
        # validator on it. When an exception is encountered on a validator,
        # remove it from the list
        methodinfos = self.instancemethodinfos.copy()
        for obj in self.iterate_model_objects():
            methodinfos = list(
                self._validate_instancemethods_for_obj(methodinfos, obj)
            )

        # clean up any remaining invalid FailingObjects
        for method_info in itertools.chain(self.instancemethodinfos, self.classmethodinfos):
            FailingObjects.objects.filter(
                content_type_id=self.model_info.content_type_id(),
                method_id=method_info.get_pk(),
                valid=False
            ).delete()

        for iminfo, summary in self.instance_summaries.items():
            # skip_failures because we already created the FailingObjects
            summary.complete()
            self._handle_summary(iminfo, summary, skip_failures=True)

    def _validate_instancemethods_for_obj(self,
                                          iminfos: List[MethodInfo],
                                          obj: models.Model
                                          ) -> Iterator[MethodInfo]:
        """ run the each data validator on the object """
        for iminfo in iminfos:
            exinfo = self._validate_instancemethod(iminfo, obj)
            if exinfo is None:
                yield iminfo
            else:
                # stop calling this validator if an exception was hit
                self.instance_summaries.pop(iminfo)
                exinfo["exc_obj_pk"] = obj.pk
                summary = Summary(_exception_info=exinfo).complete()
                self._handle_summary(iminfo, summary, skip_failures=True)

    def _validate_instancemethod(self,
                                 iminfo: MethodInfo,
                                 obj: models.Model
                                 ) -> Optional[dict]:
        """ call the data validator for a given object

         returns: the exception info if there was any
        """
        # noinspection PyBroadException
        try:
            result = iminfo.method(obj)
            exinfo = None
        except Exception:
            result = None
            exinfo = ExceptionInfoMixin.get_exception_info()

        return self._handle_result(iminfo, obj, result, exinfo)

    def _validate_classmethods(self):
        """ run all class-method validators """
        for cminfo in self.classmethodinfos:
            self._validate_classmethod(cminfo)

    def _validate_classmethod(self, cminfo: MethodInfo):
        # noinspection PyBroadException
        try:
            exinfo = None
            summary = cminfo.method()
            if isinstance(summary, Summary):
                # just to be sure the user didn't set it
                summary._exception_info = None
                summary._num_allowed_to_fail = 0
        except Exception:
            exinfo = ExceptionInfoMixin.get_exception_info()
            summary = Summary(_exception_info=exinfo).complete()

        if exinfo is None and not isinstance(summary, Summary):
            summary = Summary(_exception_info={
                "exc_type": "TypeError('classmethod data validators must "
                            "return a datavalidator.Summary')"
            })

        try:
            summary.complete()
        except AssertionError:
            summary._exception_info = ExceptionInfoMixin.get_exception_info()
            summary.complete()

        self._handle_summary(cminfo, summary)

    def _handle_result(self,
                       method_info: MethodInfo,
                       obj: models.Model,
                       result: Union[Result, bool, None],
                       exinfo: Optional[dict]
                       ) -> Optional[dict]:
        """ handle the result returned by an instance-method validator """
        extra_result_args = {}
        summary = self.instance_summaries[method_info]
        if isinstance(result, Result):
            # update the summary for each method
            if result == PASS:
                summary.num_passed += 1
            elif result == FAIL:
                summary.num_failed += 1
            else:
                summary.num_na += 1

            if result.comment:
                extra_result_args["comment"] = result.comment
            if result.allowed_to_fail is not None:
                extra_result_args["allowed_to_fail"] = result.allowed_to_fail
        elif exinfo is None:
            exinfo = {
                "exc_type": "TypeError('data validators must return datavalidator.PASS, "
                            "datavalidator.FAIL, or datavalidator.NA')",
                "exc_obj_pk": obj.pk,
            }

        if result == FAIL:
            fobj, _ = FailingObjects.objects.update_or_create(
                content_type_id=method_info.model_info.content_type_id(),
                object_pk=obj.pk,
                method_id=method_info.get_pk(),
                defaults={
                    "valid": True,
                    **extra_result_args,
                }
            )
            if len(summary.failures) < 3:
                summary.failures.append(fobj.pk)

            # if the object was (previously) marked as allowed to fail then
            # update the current summary
            if fobj.allowed_to_fail:
                summary._num_allowed_to_fail += 1

        return exinfo

    def _handle_summary(self,
                        method_info: MethodInfo,
                        summary: Optional[Summary],
                        skip_failures: bool = False
                        ) -> Summary:
        """ handle the summary returned by a class-method validator """

        vm = method_info.get_pk()
        exinfo = summary._exception_info or {}
        ValidationSummary.objects.update_or_create(
            method_id=vm,
            defaults={
                "passed": summary.passed,
                "num_passed": summary.num_passed,
                "num_failed": summary.num_failed,
                "num_na": summary.num_na,
                "num_allowed_to_fail": summary._num_allowed_to_fail,
                **exinfo,
            },
        )

        # if failures were supplied then update the ValidationResult table
        if summary.failures is not None and not skip_failures:
            ct = method_info.model_info.content_type_id()
            for obj in summary.failures:
                FailingObjects.objects.update_or_create(
                    object_pk=obj.pk,
                    content_type_id=ct,
                    method_id=vm,
                    defaults={
                        "comment": None,
                    }
                )
            summary.failures = [obj.pk for obj in summary.failures[:3]]
        self.all_summaries.append((method_info, summary))
        return summary

    def iterate_model_objects(self, chunk_size: int = 2000) -> Iterator[Any]:
        select_related_lookups = set(itertools.chain(*[
            info.select_related for info in self.instancemethodinfos
        ]))
        prefetch_related_lookups = set(itertools.chain(*[
            info.prefetch_related for info in self.instancemethodinfos
        ]))
        queryset = self.model._meta.default_manager \
                       .select_related(*select_related_lookups) \
                       .prefetch_related(*prefetch_related_lookups)
        yield from queryset_iterator(queryset, chunk_size)

    def _print_summaries(self):
        for method_info, summary in self.all_summaries:
            logger.info(
                f"\nMETHOD: {method_info.method_name}: {summary.status()}\n"
                f"'''{method_info.description}'''\n"
                f"{summary.pretty_print()}\n"
                f"-------------------------"
            )
