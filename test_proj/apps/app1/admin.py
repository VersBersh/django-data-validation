from datavalidation.admin import DataValidationMixin
from django.contrib import admin

from .models import (
    TestModel,
    CReturnValues,
    IReturnValues,
    RelatedFields,
    ModelWithExcludedParent,
)


@admin.register(TestModel)
class TestModelAdmin(DataValidationMixin, admin.ModelAdmin):
    pass


@admin.register(CReturnValues)
class CReturnValuesAdmin(DataValidationMixin, admin.ModelAdmin):
    pass


@admin.register(IReturnValues)
class IReturnValuesAdmin(DataValidationMixin, admin.ModelAdmin):
    pass


@admin.register(RelatedFields)
class RelatedFieldsAdmin(DataValidationMixin, admin.ModelAdmin):
    pass


@admin.register(ModelWithExcludedParent)
class ModelWithExcludedParentAdmin(DataValidationMixin, admin.ModelAdmin):
    pass
