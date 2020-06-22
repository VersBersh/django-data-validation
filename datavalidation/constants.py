from django.conf import settings

MAX_FAILURES_PER_MODEL = getattr(settings,
                                 "DATA_VALIDATION_MAX_FAILURES_PER_MODEL",
                                 10)

# the maximum length of the doc string of the data_validator
MAX_DESCRIPTION_LEN = getattr(settings,
                              "DATA_VALIDATION_MAX_DESCRIPTION_LEN",
                              100)

# the maximum length of a comment returned in a ValidationResult
# i.e. ValidationResult.Fail(comment="because xyz...")
MAX_RESULT_COMMENT_LEN = getattr(settings,
                                 "DATA_VALIDATION_MAX_RESULT_COMMENT_LEN",
                                 250)

MAX_TRACEBACK_LEN = 2000
