from collections import Counter
from typing import List, Tuple

from django.apps import apps
from django.core.management.base import BaseCommand
from termcolor import colored as coloured

from datavalidation.registry import REGISTRY, ValidatorInfo
from datavalidation.results import SummaryEx, Status
from datavalidation.runner import ModelValidationRunner
from datavalidation.utils import sysexit, timer
from datavalidation.logging import logger


class Command(BaseCommand):
    args = "./manage.py run_data_validation [OPTIONS]"
    help = "run data validation"

    def add_arguments(self, parser):
        parser.add_argument(
            "--models", metavar="model_name", type=str, nargs="+",
            help="a list of models to validate."
        )

    @sysexit
    @timer(output=logger.cinfo)
    def handle(self, *args, **options) -> int:
        """ run the data validation """
        model_names = options.get("models", None)
        if model_names is None:
            models = REGISTRY.keys()
        else:
            models = [apps.get_model(name) for name in model_names]

        # init runners first so that they can validate the inputs
        runners = [ModelValidationRunner(model) for model in models]

        totals = Counter()
        for runner in runners:
            summaries = runner.run()
            self.print_summaries(summaries)
            for valinfo, summary in summaries:
                totals[summary.status] += 1

        result_str = (
            f"Total Passing: {totals[Status.PASSING]}\n"
            f"Total Failing: {totals[Status.FAILING]}\n"
            f"Total Exceptions: {totals[Status.EXCEPTION]}\n"
            f"Total Uninitialized: {totals[Status.UNINITIALIZED]}\n"
        )
        if totals[Status.FAILING] + totals[Status.EXCEPTION] > 0:
            exit_code = 1
            colour = "red"
        elif totals[Status.PASSING] == 0:
            exit_code = 0
            colour = "white"
        else:
            exit_code = 0
            colour = "green"

        logger.info("="*70)
        logger.info(coloured(result_str, colour, attrs=["bold"]))
        return exit_code

    @staticmethod
    def print_summaries(summaries: List[Tuple[ValidatorInfo, SummaryEx]]):
        for valinfo, summary in summaries:
            logger.info(
                f"\nMETHOD: {valinfo.method_name}: {summary.print_status()}\n"
                f'"""{valinfo.description}"""\n'
                f"{summary.pretty_print()}\n"
                f"-------------------------"
            )
