from random import choice, seed
from typing import List

from datavalidation import data_validator, NA
from django.db import models


seed(1234)


class BaseModelManager(models.Manager):
    """ manager for creating valid and invalid data """

    def __init__(self):
        super().__init__()
        self.valid_list = list(range(10))
        self.invalid_list = list(range(10, 21))

    def generate(self, passing: int = 0, failing: int = 0, na: int = 0) -> List[models.Model]:
        """ generate testing data """
        objs = []
        for _ in range(passing):
            objs.append(self.model(foobar=choice(self.valid_list)))

        for _ in range(failing):
            objs.append(self.model(foobar=choice(self.invalid_list)))

        for _ in range(na):
            objs.append(self.model(foobar=None))

        return self.bulk_create(objs)


class BaseModel(models.Model):
    """ Base Model for pytest

     :CONDITION: foobar is less than 10 if it exists
    """
    foobar = models.PositiveIntegerField(blank=True, null=True)

    objects = BaseModelManager()

    class Meta:
        abstract = True

    def __str__(self):
        return f"foobar {self.foobar}"

    @data_validator
    def check_foobar(self):
        """ check that foobar is less than 10

         this ensures that any model that inherits BaseModel has at least
         one data_validator (otherwise it will not be added to REGISTRY)
        """
        return self.foobar < 10 if self.foobar else NA


class TestModel(BaseModel):
    __test__ = False
    pass
