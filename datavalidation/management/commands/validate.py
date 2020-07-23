from collections import Counter
from itertools import chain
from typing import List, Tuple

from django.apps import apps
from django.core.management.base import BaseCommand
from termcolor import colored as coloured

from datavalidation.registry import REGISTRY, ValidatorInfo
from datavalidation.results import SummaryEx, Status
from datavalidation.runners import ModelValidationRunner
from datavalidation.utils import sysexit, timer
from datavalidation.logging import logger


class Command(BaseCommand):
    args = "./manage.py validate [labels]"
    help = (
        "run data validation for an app, model or validator. If no "
        "arguments are provided then all apps and all models are validated."
    )

    def add_arguments(self, parser):
        help_text = (
            "a space seperated list of the form <app_label>, <app_label>."
            "<model_name> or <app_label>.<model_name>::<validator_name>"
        )
        parser.add_argument(
            "labels", nargs="*", type=str, help=help_text
        )

    @staticmethod
    def parse_label(label: str) -> List[ModelValidationRunner]:
        """ parse a command line argument """
        err_msg = (
            f"validate expects arguments the form <app_label>, <app_label>."
            f"<model_name> or <app_label>.<model_name>::<validator_name>, "
            f"got: {label}"
        )
        components = label.split(".")
        if len(components) == 1:
            app_label = components[0]
            appcfg = apps.get_app_config(app_label)
            return [
                ModelValidationRunner(model)
                for model in appcfg.models
                if model in REGISTRY
            ]
        elif len(components) == 2:
            app_label, rest = components
            rest = rest.split("::")
            model_name = rest[0]
            model = apps.get_model(app_label, model_name)
            if model not in REGISTRY:
                raise ValueError(f"{app_label}.{model_name} has nothing to validate")
            if len(rest) == 1:
                return [ModelValidationRunner(model)]
            elif len(rest) == 2:
                method_name = rest[1]
                return [ModelValidationRunner(model, method_names=[method_name])]
        raise ValueError(err_msg)

    @sysexit
    @timer(output=logger.cinfo)
    def handle(self, *args, **options) -> int:
        """ run the data validation """
        labels = options["labels"]
        if len(labels) == 0:
            # init runners first so that they can validate the inputs
            runners = [ModelValidationRunner(model) for model in REGISTRY.keys()]
        else:
            runners = list(chain(*[self.parse_label(label) for label in labels]))

        totals = Counter()
        for runner in runners:
            summaries = runner.run(show_progress=True)
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
