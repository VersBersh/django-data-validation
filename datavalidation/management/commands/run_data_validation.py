from typing import List, Tuple

from django.apps import apps
from django.core.management.base import BaseCommand
from termcolor import colored

from datavalidation.registry import REGISTRY, ValidatorInfo
from datavalidation.results import SummaryEx
from datavalidation.validator import ModelValidationRunner
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

        # init runners first so that they can validate the inputs
        runners = [ModelValidationRunner(model) for model in models]

        for runner in runners:
            summaries = runner.run()
            self.print_summaries(summaries)

    @staticmethod
    def print_summaries(summaries: List[Tuple[ValidatorInfo, SummaryEx]]):
        for valinfo, summary in summaries:
            logger.info(
                f"\nMETHOD: {valinfo.method_name}: {summary.print_status()}\n"
                f'"""{valinfo.description}"""\n'
                f"{summary.pretty_print()}\n"
                f"-------------------------"
            )
