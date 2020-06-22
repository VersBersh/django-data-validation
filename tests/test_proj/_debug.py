from datavalidation.results import Result
from datavalidation.validatior import ModelValidator
from datavalidation.models import *
from test_app.models import TestModel

ModelValidator(TestModel).validate()
