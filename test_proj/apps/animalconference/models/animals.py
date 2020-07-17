from collections import defaultdict
from pathlib import Path
from random import choice, randint

from django.db import models

from datavalidation import data_validator, PASS, FAIL, NA
from datavalidation.types import ResultType

from .habitat import Habitat


class AnimalManager(models.Manager):
    def __init__(self):
        super().__init__()
        cur_dir = Path(__file__).parent
        with (cur_dir / "lists/species.txt").open("r") as f:
            self.species = f.read().splitlines()

        self.names = defaultdict(list)
        with (cur_dir / "lists/names.txt").open("r") as f:
            for name in f.read().splitlines():
                if len(name) == 0:
                    continue
                self.names[name[0]].append(name)

        self.habitat_ids = Habitat.objects.all().values_list("id", flat=True)

    def random_animal(self) -> "Animal":
        """ return a random Animal instance for testing """
        species = choice(self.species)
        name = choice(self.names[species[0]])
        carnivorous = choice([True, False])
        predator_index = 1 if not carnivorous else randint(2, 10)
        habitat_id = choice(self.habitat_ids)
        if carnivorous:
            prey = Animal.objects.filter(predator_index=predator_index-1)[:2]
            if len(prey) == 0:
                carnivorous = False
                predator_index = 1
        else:
            prey = []
        animal = self.create(
            species=species,
            name=name,
            carnivorous=carnivorous,
            predator_index=predator_index,
            habitat_id=habitat_id,
        )
        animal.prey.set(prey)
        return animal

    def test_create(self, **kwargs) -> "Animal":
        """ create an Animal for testing """
        animal = self.random_animal()
        prey = kwargs.pop("prey", None)
        if prey is not None:
            animal.prey.set(prey)
        if len(kwargs) == 0:
            return animal
        for prop, val in kwargs.items():
            setattr(animal, prop, val)
        animal.save()
        return animal

    def populate_database(self, records: int = 100):
        """ add some data to the database """
        for _ in range(records):
            self.random_animal()


class BaseAnimal(models.Model):
    species = models.CharField(max_length=50)
    name = models.CharField(max_length=50)

    class Meta:
        abstract = True

    @data_validator
    def check_alliteration(self) -> ResultType:
        """ test that names are alliterations """
        if self.species[0] == self.name[0]:
            return PASS
        else:
            return FAIL("not an alliteration")


class Animal(BaseAnimal):
    carnivorous = models.BooleanField()
    predator_index = models.PositiveIntegerField()
    prey = models.ManyToManyField("Animal", blank=True)
    habitat = models.ForeignKey(Habitat, on_delete=models.CASCADE)

    objects = AnimalManager()

    def __str__(self):
        return f"{self.name} the {self.species}"

    @data_validator(prefetch_related="prey")
    def check_carnivorous(self) -> ResultType:
        """ test that carnivorous animals have prey and vice versa """
        if self.carnivorous:
            return self.prey.count() > 0
        else:
            return self.prey.count() == 0

    @data_validator(select_related="foobar", prefetch_related="foobaz")
    def check_no_cannibals(self) -> ResultType:
        """ check no animals are cannibalistic """
        if self.species == "Mantis":
            return FAIL(allowed_to_fail=True, comment="weirdos")
        else:
            return self not in self.prey.all()

    @data_validator(prefetch_related=["prey"])
    def check_predator_heirarchy(self) -> ResultType:
        """ check that no animals prey on other animals with a higher
            predator index
        """
        if not self.carnivorous:
            return NA
        else:
            return self.prey.filter(predator_index__gte=self.predator_index).count() == 0


class AnimalProxy(Animal):
    class Meta:
        proxy = True

    @data_validator
    def void(self):
        return PASS
