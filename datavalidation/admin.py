from functools import partial

from django.conf import settings
from django.conf.urls import url
from django.contrib import admin
from django.db import models
from django.shortcuts import render
from django.urls import include

from .viewsets import router
from .views import object_counts, csrf_info


class Summary(models.Model):
    # dummy model for the admin page
    class Meta:
        managed = False
        verbose_name_plural = "summaries"


@admin.register(Summary)
class ValidationAdmin(admin.ModelAdmin):
    def get_urls(self):
        admin_view = self.admin_site.admin_view
        if getattr(settings, "DATAVALIDATION_DEVELOPMENT", False):
            template_name = "datavalidation/dev/index.html"
        else:
            template_name = "datavalidation/index.html"
        view = partial(render, template_name=template_name)
        return [
            url(r'^api/', include(router.urls)),
            url(r'^api/meta/csrf', csrf_info),
            url(r'^api/meta/object-counts', object_counts),
            url(r'^', admin_view(view), name="datavalidation_summary_changelist"),
        ]
