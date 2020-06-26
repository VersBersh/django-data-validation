from datavalidation.results import Result
from datavalidation.validator import ModelValidator
from datavalidation.models import *
from test_app.models import TestModel
from test_app.tasks import populate_data

populate_data()

ModelValidator(TestModel).validate()

#qs = FailingObjects.objects.all()

