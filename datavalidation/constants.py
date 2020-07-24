from django.conf import settings

# the maximum length of the doc string of the data_validator
MAX_DESCRIPTION_LEN = getattr(settings,
                              "DATAVALIDATION_MAX_DESCRIPTION_LEN",
                              None)


MAX_TRACEBACK_LEN = 2000
