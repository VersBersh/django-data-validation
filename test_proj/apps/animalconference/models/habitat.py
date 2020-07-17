from random import choice
from django.db import models


class HabitatManager(models.Manager):
    habitats = [
        "forest",
        "jungle",
        "mountains",
        "ocean",
        "desert",
        "tundra",
    ]

    def random_habitat(self) -> "Habitat":
        habitat = self.create(name=choice(self.habitats))
        return habitat

    def test_create(self, **kwargs):
        habitat = self.random_habitat()
        for prop, val in kwargs.items():
            setattr(habitat, prop, val)
        habitat.save()
        return habitat

    def populate_database(self):
        for name in self.habitats:
            self.test_create(name=name)


class Habitat(models.Model):
    name = models.CharField(max_length=20)

    objects = HabitatManager()
