from datetime import datetime, timedelta as td

from django.core.management.base import BaseCommand

from animalconference.models import Animal, Seminar, Habitat


class Command(BaseCommand):
    help = "add some testing data"

    def handle(self, *args, **options) -> None:
        """ create some testing data """
        print("adding some testing data...")
        # these functions create valid data
        Habitat.objects.populate_database()
        Animal.objects.populate_database(100)
        Seminar.objects.populate_database(10)

        # create one that fails a test
        start_time = datetime.now()
        Seminar.objects.test_create(
            start_time=start_time, end_time=start_time - td(hours=1)
        )
