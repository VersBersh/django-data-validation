import sys
import traceback
from typing import Optional, Dict

import enumfields
from django.contrib.contenttypes.models import ContentType
from django.db import models

from .constants import (
    MAX_DESCRIPTION_LEN,
    MAX_TRACEBACK_LEN,
)
from .registry import REGISTRY, ModelInfo
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
    num_failing = models.PositiveIntegerField(blank=True, null=True)
    num_na = models.PositiveIntegerField(blank=True, null=True)

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='+',
    )

    class Meta:
        index_together = ("content_type", "method_name")
        unique_together = ("content_type", "method_name")
        ordering = ("app_label", "model_name", "method_name")

    def __str__(self):
        return f"Validator {self.method_name}: {self.status.name}"

    @property
    def num_allowed_to_fail(self):
        return self.failing_objects.filter(allowed_to_fail=True).count()

    @property
    def model_info(self) -> Optional[ModelInfo]:
        """ return the ModelInfo that this record represents """
        model = self.content_type.model_class()
        if model in REGISTRY:
            return REGISTRY[model]


class FailingObject(models.Model):
    """ objects that did not pass data validation """
    validator = models.ForeignKey(
        Validator,
        on_delete=models.CASCADE,
        related_name="failing_objects",
        db_index=True,
    )
    object_pk = models.PositiveIntegerField()

    comment = models.TextField(blank=True)

    # manual entry by User - this object is allowed to fail validation
    allowed_to_fail = models.BooleanField(default=False)
    allowed_to_fail_justification = models.TextField(blank=True)

    # control variable: existing records are marked as invalid prior to
    # running the validation so that objects that have been marked
    # allowed_to_fail by the user are not deleted
    valid = models.BooleanField()

    class Meta:
        index_together = ("validator", "object_pk")
        unique_together = ("validator", "object_pk")
        ordering = ("object_pk",)

    def __str__(self):
        return f"FailingObject: {self.validator.method_name} ({self.object_pk})"
