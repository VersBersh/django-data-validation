from typing import List, TYPE_CHECKING, Optional

from django.contrib import admin
from django.contrib.admin.helpers import InlineAdminFormSet
from django.contrib.contenttypes.admin import GenericTabularInline
from django.contrib.contenttypes.forms import BaseGenericInlineFormSet
from django.core.checks import messages
from django.db import models
from django.forms import Textarea
from django.http import HttpRequest, QueryDict
from django.utils.safestring import mark_safe

from datavalidation.models import FailingObject
from datavalidation.registry import RegistryKeyError
from datavalidation.runners import ObjectValidationRunner
from datavalidation.utils import partition


class BaseFormSet(BaseGenericInlineFormSet):
    is_exception: bool = None

    def get_queryset(self):
        if not hasattr(self, "_queryset"):
            self._queryset = super().get_queryset().filter(  # noqa
                is_exception=self.is_exception, is_valid=True
            )
        return self._queryset

    @property
    def count(self):
        return len(self.get_queryset())


class DataValidationExceptionFormSet(BaseFormSet):
    is_exception = True


class DataValidationFailureFormSet(BaseFormSet):
    is_exception = False


class BaseDataValidationInline(GenericTabularInline):
    class Media:
        css = {"all": ("datavalidation/admin_mixin/datavalidation-admin-mixin.css",)}

    template = "datavalidation/admin_mixin/tabular.html"

    model = FailingObject
    ct_field = "content_type"
    ct_fk_field = "object_pk"

    can_delete = False
    max_num = 0

    formfield_overrides = {
        models.TextField: {
            "widget": Textarea(attrs={
                "rows": 1, "style": "width: 95%; resize: vertical; min-height: 1.25em"
            })
        },
    }

    @staticmethod
    def _description(obj: FailingObject) -> str:
        return mark_safe(obj.validator.description)

    @staticmethod
    def _comment(obj: FailingObject) -> str:
        return mark_safe(obj.comment)


class DataValidationFailureInline(BaseDataValidationInline):
    formset = DataValidationFailureFormSet
    html_classes = "datavalidation-inline datavalidation-failure"
    verbose_name = "Data Validation Failure"
    verbose_name_plural = "Data Validation Failures"
    fields = ("_description", "_comment", "allowed_to_fail", "allowed_to_fail_justification")
    readonly_fields = ("_description", "_comment")


class DataValidationExceptionInline(BaseDataValidationInline):
    formset = DataValidationExceptionFormSet
    html_classes = "datavalidation-inline datavalidation-exception"
    verbose_name = "Data Validation Exception"
    verbose_name_plural = "Data Validation Exceptions"
    fields = ("_description", "_comment")
    readonly_fields = ("_description", "_comment")


if TYPE_CHECKING:
    _Base = admin.ModelAdmin
else:
    _Base = object


class DataValidationMixin(_Base):
    # to ensure that the data validation formset sits at the top of the
    # page we have to override the admin template. If the user also has a
    # custom admin template then they will need to add the line:
    # {% include "datavalidation/admin_mixin/datavalidation_inline.html" %}
    # to their custom template
    change_form_template = "datavalidation/admin_mixin/change_form.html"

    def validate_object(self, request: HttpRequest, obj: models.Model) -> None:
        # run data validation if posting new data. We run validation here
        # rather than in full_clean because we need the object and it's
        # related failing objects have been saved to the database already.
        assert request.method == "POST"
        assert obj is not None
        try:
            _, failing, exception = ObjectValidationRunner(obj).run(class_methods=True)
        except RegistryKeyError:
            # the model has no validators. Adding DataValidationMixin to
            # the admin provides no benefit, but it shouldn't crash
            failing, exception = 0, 0
        if failing != 0:
            post: QueryDict = request.POST.copy()  # noqa
            post.pop("_save", None)
            post["_continue"] = ["Save and continue editing"]
            request.POST = post
            self.message_user(
                request,
                message=mark_safe("this object failed data validation"),
                level=messages.WARNING
            )
        elif exception != 0:
            self.message_user(
                request,
                message=mark_safe("one or more data validators hit an exception"),
                level=messages.ERROR
            )

    def response_change(self, request: HttpRequest, obj: models.Model):
        self.validate_object(request, obj)
        return super().response_change(request, obj)

    def response_add(self, request: HttpRequest, obj: models.Model, *args, **kwargs):
        self.validate_object(request, obj)
        return super().response_add(request, obj, *args, **kwargs)

    def get_inline_instances(self, request: HttpRequest, obj: Optional[models.Model] = None):
        # inject DataValidationInline here so that the ModelAdmin will do
        # the processing required to include the inline in the change form
        # n.b. in Django 3.0 we can use the get_inline hook instead
        inline_instances = super().get_inline_instances(request, obj)
        for inline_class in [DataValidationFailureInline, DataValidationExceptionInline]:
            inline = inline_class(self.model, self.admin_site)
            inline.max_num = 0
            inline_instances.append(inline)
        return inline_instances

    def render_change_form(self, request: HttpRequest, context: dict, *args, **kwargs):
        # here we extract the formset for DataValidationInline, which the
        # model admin has processed for us and update the context dict
        formsets: List[InlineAdminFormSet] = context["inline_admin_formsets"]
        datavalidation_formsets, other_formsets = partition(
            formsets, lambda fs: isinstance(fs.opts, BaseDataValidationInline)
        )
        context.update({
            "datavalidation_formsets": datavalidation_formsets,
            "inline_admin_formsets": other_formsets,
        })
        return super().render_change_form(request, context, *args, **kwargs)
