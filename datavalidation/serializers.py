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
    def get_admin_page(obj: FailingObject):
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
