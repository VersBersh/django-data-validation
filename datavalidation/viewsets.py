from rest_framework import viewsets, permissions

from .models import FailingObjects, Validator
from .serializers import FailingObjectSerializer, ValidatorSerializer


class FailingObjectViewSet(viewsets.ModelViewSet):
    serializer_class = FailingObjectSerializer
    queryset = FailingObjects.objects.all()
    permission_classes = [
        permissions.AllowAny
    ]


class ValidatorViewSet(viewsets.ModelViewSet):
    serializer_class = ValidatorSerializer
    queryset = Validator.objects.all()
    permission_classes = [
        permissions.AllowAny
    ]
