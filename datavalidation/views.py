import re

from django.apps import apps
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.db import OperationalError
from django.http import (
    HttpResponse, HttpResponseBadRequest, Http404, HttpResponseServerError,
    JsonResponse
)
from django.views.decorators.http import require_GET


@login_required
@require_GET
def object_counts(request):
    """ return the number of records of a particular model """
    try:
        app_label = request.GET["appLabel"]
        model_name = request.GET["modelName"]
    except KeyError:
        return HttpResponseBadRequest("expecting parameters appLabel and modelName")

    try:
        model = apps.get_model(app_label, model_name)
    except LookupError:
        raise Http404(f"{app_label}.{model_name} does not exist")

    try:
        total = model._meta.default_manager.count()  # noqa
    except OperationalError:
        return HttpResponseServerError()

    return HttpResponse(bytes(str(total), "utf-8"))


@login_required
@require_GET
def csrf_info(request):
    """ return the CSRF settings """
    # https://docs.djangoproject.com/en/2.2/ref/settings/#std:setting-CSRF_HEADER_NAME
    # refer to above link about transforming CSRF_HEADER_NAME
    csrf_header_name = getattr(settings, "CSRF_HEADER_NAME", "")
    csrf_header_name = re.sub("^HTTP_", "", csrf_header_name).replace("_", "-")
    return JsonResponse({
        "csrf_cookie_name": getattr(settings, "CSRF_COOKIE_NAME", ""),
        "csrf_header_name": csrf_header_name,
    })
