import sys
import traceback
from typing import TYPE_CHECKING, Type

import enumfields
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import QuerySet
from django.urls import reverse, NoReverseMatch

from .constants import (
    MAX_DESCRIPTION_LEN,
    MAX_TRACEBACK_LEN,
)
from .results import ExceptionInfo, Status


__all__ = (
    "DataValidationMixin",
    "FailingObject",
    "Validator",
)


class ExceptionInfoMixin(models.Model):
    exc_type = models.TextField(
        blank=True, null=True,
        default=None
    )
    exc_traceback = models.TextField(
        max_length=MAX_TRACEBACK_LEN,
        blank=True, null=True,
        default=None
    )
    exc_obj_pk = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        abstract = True

    @classmethod
    def get_exception_info(cls) -> ExceptionInfo:
        """ return the exception info of the current exception

         call this method while handling an exception. If called outside
         the excption clause it returns the field values of None
        """
        _, exc, tb = sys.exc_info()
        *top_frames, last_frame = traceback.format_list(traceback.extract_tb(tb))
        tb_str = last_frame[-MAX_TRACEBACK_LEN:]
        for frame in reversed(top_frames):
            if len(frame) + len(tb_str) <= MAX_TRACEBACK_LEN:
                tb_str = f"{frame}\n{tb_str}"
            else:
                break
        return ExceptionInfo(
            exc_type=repr(exc),
            exc_traceback=tb_str
        )


class Validator(ExceptionInfoMixin, models.Model):
    """ methods that are data validators """
    app_label = models.CharField(max_length=100)
    model_name = models.CharField(max_length=100)
    method_name = models.CharField(max_length=100)
    description = models.TextField(max_length=MAX_DESCRIPTION_LEN)

    last_run_time = models.DateTimeField(blank=True, null=True)
    execution_time = models.FloatField(blank=True, null=True)
    status = enumfields.EnumIntegerField(Status, default=Status.UNINITIALIZED)
    num_passing = models.PositiveIntegerField(blank=True, null=True)
    num_na = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        index_together = ("app_label", "model_name", "method_name")
        unique_together = ("app_label", "model_name", "method_name")
        ordering = ("app_label", "model_name", "method_name")

    def __str__(self):
        return f"{self.model_name}.{self.method_name}: {self.status.name}"

    def get_num_failing(self):
        return self.failing_objects.count()

    def get_num_allowed_to_fail(self):
        return self.failing_objects.filter(allowed_to_fail=True).count()

    @classmethod
    def get_status_for_model(cls, model: Type[models.Model]) -> Status:
        """ return the datavalidation status for the model """
        app_label = model._meta.app_label
        model_name = model.__name__
        statuses = cls.objects \
                      .filter(app_label=app_label, model_name=model_name) \
                      .values_list("status", flat=True)
        model_status: Status = Status.UNINITIALIZED
        for status in statuses:
            if status == Status.PASSING and model_status == Status.UNINITIALIZED:
                model_status = Status.PASSING
            elif status == Status.FAILING:
                model_status = Status.FAILING
            if status == Status.EXCEPTION:
                return Status.EXCEPTION
        return model_status


class FailingObjectManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_valid=True)


class FailingObject(models.Model):
    """ objects that did not pass data validation """
    validator = models.ForeignKey(
        Validator,
        on_delete=models.CASCADE,
        related_name="failing_objects",
        db_index=True,
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='+',
    )
    object_pk = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_pk")
    is_exception = models.BooleanField()

    comment = models.TextField(blank=True)

    # manual entry by User - this object is allowed to fail validation
    allowed_to_fail = models.BooleanField(default=False)
    allowed_to_fail_justification = models.TextField(blank=True, verbose_name="justification")

    # control variable: existing records are marked as invalid prior to
    # running the validation so that objects that have been marked
    # allowed_to_fail by the user are not deleted
    is_valid = models.BooleanField()

    objects = FailingObjectManager()
    all_objects = models.Manager()

    class Meta:
        index_together = ("validator", "object_pk")
        unique_together = ("validator", "object_pk")
        ordering = ("object_pk",)

    def __str__(self):
        return f"{self.validator.model_name} ({self.object_pk}) [{self.validator.method_name}]"

    @property
    def admin_page(self) -> str:
        app_label = self.validator.app_label
        model_name = self.validator.model_name.lower()
        try:
            return reverse(f"admin:{app_label}_{model_name}_change", args=(self.object_pk,))
        except NoReverseMatch:
            return ""

    @classmethod
    def get_for_object(cls, obj: models.Model):
        """ return the failing objects for a given object """
        ct = ContentType.objects.get_for_model(obj._meta.model)
        return FailingObject.objects.filter(
            content_type=ct, object_pk=obj.pk
        )

    @classmethod
    def get_for_objects(cls, queryset: QuerySet) -> QuerySet:
        """ return the failing objects for all objects in a queryset """
        ct = ContentType.objects.get_for_model(queryset.model)
        return FailingObject.objects.filter(
            content_type=ct, object_pk__in=queryset.values_list("pk", flat=True)
        )


if TYPE_CHECKING:
    _Base = models.Model
else:
    _Base = object


class DataValidationMixin(_Base):
    @property
    def datavalidation_results(self) -> QuerySet:
        """ returns the FailingObjects for a given object """
        return FailingObject.get_for_object(self)

    @property
    def datavalidation_passing(self) -> bool:
        """ returns True is datavalidation status is PASSING for the object """
        return FailingObject.get_for_object(self).filter(allowed_to_fail=False).count() == 0

    @classmethod
    def datavalidation_status(cls) -> Status:
        """ return the datavalidation status for the model """
        return Validator.get_status_for_model(cls)
