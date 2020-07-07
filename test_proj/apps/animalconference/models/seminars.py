from datetime import datetime, timedelta as td
from pathlib import Path
from random import choice, randint

from django.db import models
from django.db.models import F, QuerySet

from datavalidation import data_validator, Summary, ResultType
from .animals import Animal


class SeminarManager(models.Manager):
    def __init__(self):
        super().__init__()
        cur_dir = Path(__file__).parent
        with (cur_dir / "lists/topics.txt").open("r") as f:
            self.topics = f.read().split("\n")

        self.CONFERENCE_START = datetime.now()

    def random_seminar(self) -> "Seminar":
        """ return a random Seminar instance for testing """
        animal_ids = (Animal.objects
                            .filter(carnivorous=True)
                            .values_list("id", flat=True))
        host = Animal.objects.get(id=choice(animal_ids))
        start_time = self.CONFERENCE_START + td(hours=randint(0, 72))
        end_time = start_time + td(minutes=choice([30, 60, 90]))
        seminar = self.create(
            topic=self.topics[Seminar.objects.count()],
            host=host,
            start_time=start_time,
            end_time=end_time
        )
        # picking attendees with the same predator index to ensure that
        # no one eats another attendee
        attendees = (Animal.objects
                           .filter(predator_index=host.predator_index)
                           .exclude(id=host.id)[:Seminar.MAX_ATTENDEES])
        seminar.attendees.set(attendees)
        return seminar

    def test_create(self, **kwargs):
        """ create an Seminar for testing """
        seminar = self.random_seminar()
        attendees = kwargs.pop("attendees", None)
        if attendees is not None:
            seminar.attendees.set(attendees)
        if len(kwargs) == 0:
            return seminar
        for prop, val in kwargs.items():
            setattr(seminar, prop, val)
        seminar.save()
        return seminar

    def populate_database(self, records: int = 10):
        """ populate the database with valid data """
        for _ in range(records):
            self.random_seminar()


class Seminar(models.Model):
    MAX_ATTENDEES = 10

    topic = models.TextField()
    host = models.ForeignKey(
        Animal, related_name="seminars_hosting", on_delete=models.CASCADE
    )
    attendees = models.ManyToManyField(
        Animal, related_name="seminars_attending"
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(blank=True, null=True)

    objects = SeminarManager()

    def __str__(self):
        return self.topic

    @data_validator(select_related="host")
    def check_host_is_carnivorous(self) -> ResultType:
        """ only carnivorous hosts at this conference apparently """
        return self.host.carnivorous

    @classmethod
    @data_validator
    def check_start_time_before_end_time(cls) -> QuerySet:
        # returning the failures as a queryset
        return cls.objects.filter(start_time__gt=F("end_time"))

    @classmethod
    @data_validator
    def check_max_attendees(cls) -> Summary:
        """ check that each seminar has at most 10 attendees """
        summary = Summary()
        for seminar in cls.objects.prefetch_related("attendees"):
            if seminar.attendees.count() > cls.MAX_ATTENDEES:
                summary.num_failing += 1
                summary.failures.append(seminar)
            else:
                summary.num_passing += 1
        return summary

    @data_validator
    def check_instancemethod_hits_an_exception(self) -> ResultType:
        """ testing the user's code hitting an exception in an instance
            method
        """
        raise ValueError("instancemethod hit an exception")

    @classmethod
    @data_validator
    def check_classmethod_hits_an_exception(cls) -> Summary:
        """ testing the user's code hitting an exception in a class method """
        raise ValueError("classmethod hit an exception")

    @data_validator
    def check_return_none(self) -> ResultType:
        """ testing the user returning the wrong type """
        return None

    @classmethod
    @data_validator
    def check_return_silent(cls) -> ResultType:
        """ testing the silently returning """
        pass

    @classmethod
    @data_validator
    def check_return_inconsistent_summary(cls) -> Summary:
        """ when the user returns an inconsistent Summary object """
        return Summary(num_failing=True)
