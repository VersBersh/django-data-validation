import sys
import traceback
from typing import Optional, Dict

import enumfields
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction
from django.urls import reverse, NoReverseMatch

from .constants import (
    MAX_DESCRIPTION_LEN,
    MAX_TRACEBACK_LEN,
)
from .results import Status


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
    def get_exception_info(cls) -> Dict[str, Optional[str]]:
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
        return dict(
            exc_type=repr(exc),
            exc_traceback=tb_str
        )


class Validator(ExceptionInfoMixin, models.Model):
    """ methods that are data validators """
    app_label = models.CharField(max_length=100)
    model_name = models.CharField(max_length=100)
    method_name = models.CharField(max_length=100)
    description = models.TextField(max_length=MAX_DESCRIPTION_LEN)
    is_class_method = models.BooleanField()

    last_run_time = models.DateTimeField(blank=True, null=True)
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
    @transaction.atomic
    def refresh_statuses(cls, classmethods_only: bool = False):
        """ recalculate the status from the failing objects

         A status might need to be recalculated if an object is updated or
         a failing object is marked allowed to fail. If Validators are
         currently marked as UNINITIALIZED or EXCEPTION then the new status
         cannot be determined by counting the number of failing objects so
         they are not updated
        """
        validators = cls.objects.exclude(status__in=[Status.UNINITIALIZED, Status.EXCEPTION])
        if classmethods_only:
            validators = validators.filter(is_class_method=True)

        for validator in validators.prefetch_related("failing_objects").select_for_update():
            if len(validator.failing_objects.filter(allowed_to_fail=False)) == 0:
                new_status = Status.PASSING
            else:
                new_status = Status.FAILING
            if validator.status != new_status:
                validator.status = new_status
                validator.save()


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
