import sys
import logging
logger = logging.getLogger("datavalidation")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(message)s")
handler.formatter = formatter
logger.addHandler(handler)
