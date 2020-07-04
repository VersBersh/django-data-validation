from django.conf import settings

MAX_FAILURES_PER_MODEL = getattr(settings,
                                 "DATA_VALIDATION_MAX_FAILURES_PER_MODEL",
                                 10)

# the maximum length of the doc string of the data_validator
MAX_DESCRIPTION_LEN = getattr(settings,
                              "DATA_VALIDATION_MAX_DESCRIPTION_LEN",
                              100)


MAX_TRACEBACK_LEN = 2000
