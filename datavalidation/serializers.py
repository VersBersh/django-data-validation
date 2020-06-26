from rest_framework.serializers import ModelSerializer

from .models import Validator, FailingObjects


class FailingObjectSerializer(ModelSerializer):
    class Meta:
        model = FailingObjects
        fields = "__all__"


class ValidatorSerializer(ModelSerializer):
    class Meta:
        model = Validator
        fields = "__all__"
