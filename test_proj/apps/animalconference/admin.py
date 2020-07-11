from django.contrib import admin

from datavalidation.admin import DataValidationMixin

from .models import Animal, Seminar


@admin.register(Animal)
class AnimalAdmin(DataValidationMixin, admin.ModelAdmin):
    pass


@admin.register(Seminar)
class SeminarAdmin(DataValidationMixin, admin.ModelAdmin):
    pass
