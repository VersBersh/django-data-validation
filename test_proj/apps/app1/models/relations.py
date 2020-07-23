from random import choice, sample, seed
from typing import List

from datavalidation import data_validator, PASS, FAIL, NA
from django.db import models

from .base import BaseModel


seed(1234)


class Relation(BaseModel):
    fkey = models.ForeignKey(
        "RelatedFields", on_delete=models.CASCADE, blank=True, null=True
    )

    class TestData:
        ORDER = 1  # generate data on this model first


class RelatedFieldsManager(models.Manager):
    def generate(self, passing: int = 0) -> List["RelatedFields"]:
        """ generate objects with related fields """

        relatives = sorted(Relation.objects.all().values_list("id", flat=True))
        existing = RelatedFields.objects.count()
        assert existing + passing <= len(relatives)

        # add relations: RelatedFields -> Relation
        objs = []
        for ix in range(existing, existing + passing):
            objs.append(RelatedFields(
                o2o_id=relatives[ix],
                fkey_id=relatives[-ix],
            ))
        objs = self.bulk_create(objs)

        # add M2M relations
        for obj in objs:
            obj.m2m.set(sample(relatives, k=4))

        # add relations: Relation -> RelatedFields
        updated = []
        for relative in Relation.objects.all():
            if choice([True, False]):
                relative.fkey = choice(objs)
                updated.append(relative)
        Relation.objects.bulk_update(updated, fields=["fkey"])

        return objs


class RelatedFields(models.Model):
    """ Models with Related Fields

    tests: related fields with select_related/prefetch_related
    """
    o2o = models.OneToOneField(
        Relation, on_delete=models.CASCADE, related_name="o2o_relation"
    )
    fkey = models.ForeignKey(
        Relation, on_delete=models.CASCADE, related_name="fkey_relation"
    )
    m2m = models.ManyToManyField(Relation, through="RelatedFieldsM2M")

    objects = RelatedFieldsManager()

    class TestData:
        ORDER = 2  # generate data on this model second

    @data_validator(select_related="o2o")
    def select_related_o2o(self):
        """ tests: select_related on OneToOneField """
        if self.o2o.foobar is None:
            return NA
        return self.o2o.foobar < 10

    @data_validator(select_related=["fkey"])
    def select_related_fkey(self):
        """ tests: select_related on ForeignKey """
        if self.fkey.foobar is None:
            return NA
        return self.o2o.foobar < 10

    @data_validator(select_related="fkey__o2o_realtion__fkey")
    def select_related_multi(self):
        """ tests select_related with multiple levels """
        foobar = self.fkey.o2o_relation.fkey.foobar
        if foobar is None:
            return NA
        return foobar < 10

    @data_validator(prefetch_related="relation_set")
    def prefetch_related_rev_fkey(self):
        """ tests: prefetch_related on a ReverseForeignKey """
        return self.relation_set.filter(foobar__gte=10).count() == 0

    @data_validator(prefetch_related="m2m")
    def prefetch_related_m2m(self):
        """ tests: prefetch_related on a ManyToManyField """
        if self.m2m.count() == 4:
            return PASS
        return FAIL

    @data_validator(select_related="wibble", prefetch_related="wobble")
    def bad_related_names(self):
        """ tests: user has used invalid select_related and
            prefetch_related fields
        """
        return PASS

    @classmethod
    @data_validator(select_related=["fkey"])
    def useless_select_related(cls):
        """ test select_related with classmethod doesn't raise error
            (even if it does nothing)
        """
        return PASS


class RelatedFieldsM2M(models.Model):
    class TestData:
        NO_GENERATE = True
    rf = models.ForeignKey(RelatedFields, blank=True, null=True, on_delete=models.SET_NULL)
    rl = models.ForeignKey(Relation, blank=True, null=True, on_delete=models.SET_NULL)
