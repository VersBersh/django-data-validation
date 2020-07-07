from django.contrib import admin

from .models import Animal, Seminar


@admin.register(Animal)
class AnimalAdmin(admin.ModelAdmin):
    pass


@admin.register(Seminar)
class SeminarAdmin(admin.ModelAdmin):
    pass
