import sys
import traceback
from typing import Optional, Dict

from django.contrib.contenttypes.models import ContentType
from django.db import models

from .constants import (
    MAX_DESCRIPTION_LEN,
    MAX_RESULT_COMMENT_LEN,
    MAX_TRACEBACK_LEN,
)
from .registry import REGISTRY, ModelInfo
from .results import Summary


class ExceptionInfoMixin(models.Model):
    exc_type = models.CharField(
        max_length=250,
        blank=True, null=True,
        default=None
    )
    traceback = models.TextField(
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
            traceback=tb_str
        )


class Validator(ExceptionInfoMixin, models.Model):
    """ methods that are data validators """
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='+',
    )
    method_name = models.CharField(max_length=80)
    description = models.TextField(max_length=MAX_DESCRIPTION_LEN)
    is_class_method = models.BooleanField()

    last_run_time = models.DateTimeField(blank=True, null=True)
    passed = models.BooleanField(blank=True, null=True)
    num_passed = models.PositiveIntegerField(blank=True, null=True)
    num_failed = models.PositiveIntegerField(blank=True, null=True)
    num_na = models.PositiveIntegerField(blank=True, null=True)
    num_allowed_to_fail = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        index_together = ("content_type", "method_name")
        unique_together = ("content_type", "method_name")

    def __str__(self):
        status = Summary.status(self, colour=False)  # noqa
        return f"ValidationSummary {self.method_name}: {status}"

    @property
    def model_info(self) -> Optional[ModelInfo]:
        """ return the ModelInfo that this record represents """
        model = self.content_type.model_class()
        if model in REGISTRY:
            return REGISTRY[model]


class FailingObjects(models.Model):
    """ objects that did not pass data validation """
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='+'
    )
    object_pk = models.PositiveIntegerField()

    method = models.ForeignKey(
        Validator,
        on_delete=models.CASCADE,
        related_name="failing_objects",
        db_index=True,
    )

    comment = models.TextField(max_length=MAX_RESULT_COMMENT_LEN)

    # manual entry by User - this test is allowed to fail
    allowed_to_fail = models.BooleanField(default=False)

    # control variable: existing records are marked as invalid prior to
    # running the validation so that objects that have been marked
    # allowed_to_fail by the user are not deleted
    valid = models.BooleanField()

    class Meta:
        index_together = ("content_type", "object_pk", "method")
        unique_together = ("content_type", "object_pk", "method")

    def __str__(self):
        return f"ValidationResult: {self.method.method_name} ({self.object_pk})"
