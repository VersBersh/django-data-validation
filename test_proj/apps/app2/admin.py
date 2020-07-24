from datavalidation.admin import DataValidationMixin
from django.contrib import admin

from .models import SecondDatabase


@admin.register(SecondDatabase)
class SecondDatabaseAdmin(DataValidationMixin, admin.ModelAdmin):
    pass
