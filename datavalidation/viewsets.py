from django.db.models import QuerySet
from rest_framework import viewsets, permissions, pagination, routers

from .models import FailingObject, Validator
from .serializers import FailingObjectSerializer, ValidatorSerializer


class FailingObjectPagination(pagination.PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'


class FailingObjectViewSet(viewsets.ModelViewSet):
    serializer_class = FailingObjectSerializer
    pagination_class = FailingObjectPagination
    queryset = FailingObject.objects.all()
    permission_classes = [
        permissions.IsAuthenticated
    ]

    def get_queryset(self) -> QuerySet:
        validator_id = self.request.query_params.get("validator_id")
        if validator_id is None:
            return FailingObject.objects.all().order_by("id")
        return FailingObject.objects.filter(validator_id=validator_id)


class ValidatorViewSet(viewsets.ModelViewSet):
    serializer_class = ValidatorSerializer
    queryset = Validator.objects.prefetch_related("failing_objects")
    permission_classes = [
        permissions.IsAuthenticated
    ]


router = routers.DefaultRouter()
router.register(r"failing-objects", FailingObjectViewSet)
router.register(r"validator-summary", ValidatorViewSet)




