from typing import Optional

from django.urls import reverse, NoReverseMatch
from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers

from .models import Validator, FailingObject


class FailingObjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = FailingObject
        exclude = ("valid",)

    admin_page = serializers.SerializerMethodField("get_admin_page")

    @staticmethod
    def get_admin_page(obj: FailingObject) -> str:
        app_label = obj.validator.app_label.lower()
        model_name = obj.validator.model_name.lower()
        try:
            return reverse(f"admin:{app_label}_{model_name}_change", args=(obj.object_pk,))  # noqa E501
        except NoReverseMatch:
            return ""


class ValidatorSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Validator
        exclude = ("content_type",)

    num_allowed_to_fail = serializers.ReadOnlyField()
    num_failing = serializers.SerializerMethodField("get_num_failing")

    @staticmethod
    def get_num_failing(obj: Validator) -> Optional[int]:
        # if Validator.num_failing is None, but there are FailingObjects
        # (e.g. because the validator is a classmethod that returns a
        # QuerySet), then we return the number of FailingObjects
        if obj.num_failing is None:
            count = obj.failing_objects.count()
            if count > 0:
                return count
        return obj.num_failing
