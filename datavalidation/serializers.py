from enumfields.drf import EnumSupportSerializerMixin
from rest_framework import serializers

from .models import Validator, FailingObject


class FailingObjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = FailingObject
        exclude = ("valid",)

    admin_page = serializers.ReadOnlyField()


class ValidatorSerializer(EnumSupportSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Validator
        exclude = ("content_type",)

    num_failing = serializers.ReadOnlyField()
    num_allowed_to_fail = serializers.ReadOnlyField()
