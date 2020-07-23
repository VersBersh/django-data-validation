from functools import reduce
from typing import Any

from django.apps import apps
from django.core.management.base import BaseCommand


def dgetattr(obj: Any, attr: str, default: Any) -> Any:
    """ getattr with dot seperated attribute list """
    try:
        return reduce(getattr, attr.split("."), obj)
    except AttributeError:
        return default


class Command(BaseCommand):
    help = "add some testing data"

    def add_arguments(self, parser):
        parser.add_argument(
            "num_passing", type=int, nargs="?", default=100,
            help="number of passing record to create per model"
        )

        parser.add_argument(
            "--exact", action="store_true", default=False,
            help="ensure the model has exactly `num_passing` records"
        )

    def handle(self, *args, **options) -> None:
        """ create some testing data """
        num_passing = options.get("num_passing")
        exact = options.get("exact")
        print("adding some testing data...")
        for app_label in ("app1", "app2"):
            models = apps.get_app_config(app_label).models.values()
            for model in sorted(models, key=lambda m: dgetattr(m, "TestData.ORDER", 0)):
                if dgetattr(model, "TestData.NO_GENERATE", False):
                    continue
                if exact:
                    count = model.objects.count()
                    if count == num_passing:
                        continue
                    else:
                        print(f"deleting {count} objects from {model.__name__}")
                        model.objects.all().delete()
                gen = getattr(model.objects, "generate", None)
                if gen is not None:
                    gen(passing=num_passing)
