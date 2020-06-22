from django.apps import apps
from django.core.management.base import BaseCommand
from termcolor import colored

from datavalidation.registry import REGISTRY
from datavalidation.validatior import ModelValidator
from datavalidation.utils import timer
from datavalidation.logging import logger


class Command(BaseCommand):
    args = "./manage.py run_data_validation [OPTIONS]"
    help = "run data validation"

    def add_arguments(self, parser):
        parser.add_argument(
            "--models", metavar="model_name", type=str, nargs="+",
            help="a list of models to validate."
        )

    @timer(output=lambda s: logger.info(colored(s, "yellow")))
    def handle(self, *args, **options):
        """ run the data validation """
        model_names = options.get("models", None)
        if model_names is None:
            models = REGISTRY.keys()
        else:
            models = [apps.get_model(name) for name in model_names]
            for model in models:
                if model not in REGISTRY:
                    raise ValueError(f"{model.__name__} has no data validators")

        for validator in [ModelValidator(model) for model in models]:
            validator.validate()

