from django.contrib import admin

from .models import (
    TestModel,
    CReturnValues,
    IReturnValues,
    RelatedFields,
    ModelWithExcludedParent,
)


@admin.register(TestModel)
class TestModelAdmin(admin.ModelAdmin):
    pass


@admin.register(CReturnValues)
class CReturnValuesAdmin(admin.ModelAdmin):
    pass


@admin.register(IReturnValues)
class IReturnValuesAdmin(admin.ModelAdmin):
    pass


@admin.register(RelatedFields)
class RelatedFieldsAdmin(admin.ModelAdmin):
    pass


@admin.register(ModelWithExcludedParent)
class ModelWithExcludedParentAdmin(admin.ModelAdmin):
    pass
