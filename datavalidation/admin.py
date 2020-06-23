from functools import partial

from django.conf import settings
from django.conf.urls import url
from django.contrib import admin
from django.db import models
from django.shortcuts import render


class Summary(models.Model):
    # dummy model for the admin page
    class Meta:
        managed = False
        verbose_name_plural = "summaries"


@admin.register(Summary)
class ValidationAdmin(admin.ModelAdmin):
    def get_urls(self):
        name = "datavalidation_summary_changelist"
        is_dev_mode = getattr(settings, "DATAVALIDATION_DEVELOPMENT", False)
        mode = "dev" if is_dev_mode else "prod"
        template_name = f"datavalidation/{mode}/index.html"
        context = {"mode": mode}
        view = partial(render, template_name=template_name, context=context)
        return [
            url('', self.admin_site.admin_view(view), name=name)
        ]
