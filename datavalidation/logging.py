import sys
import logging

from termcolor import colored


class ColouredLogger(logging.Logger):
    def cdebug(self, message: str) -> None:
        self.debug(colored(message, color="magenta"))

    def cinfo(self, message: str) -> None:
        self.info(colored(message, color="cyan", attrs=["bold"]))

    def cwarning(self, message: str) -> None:
        self.warning(colored(message, color="yellow"))

    def cerror(self, message: str) -> None:
        self.error(colored(message, color="red", attrs=["bold"]))


logger = logging.getLogger("datavalidation")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.formatter = logging.Formatter("%(message)s")
logger.addHandler(handler)

logger.__class__ = ColouredLogger
