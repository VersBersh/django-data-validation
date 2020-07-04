from django.db import models

from datavalidation import data_validator, PASS, FAIL, NA, Summary


class TestModel(models.Model):
    even_number = models.IntegerField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(blank=True, null=True)
    limit = models.IntegerField()
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"TestModel {self.even_number} {self.limit}"

    @data_validator
    def test_date_range(self):
        """ check that start date is not after end date """
        if not self.end_date:
            return NA("end_date undefined")
        elif self.start_date <= self.end_date:
            return PASS
        else:
            return FAIL

    @classmethod
    @data_validator
    def test_numbers_even(cls):
        """ check that all numbers are even """
        failures = []
        summary = Summary()
        for obj in cls.objects.all():
            if obj.even_number % 2 != 0:
                failures.append(obj.pk)
                summary.num_failing += 1
            else:
                summary.num_passing += 1
        return summary

    @classmethod
    @data_validator
    def simple_class_validator(cls):
        """ just return PASS """
        return PASS

    @data_validator
    def test_limit(self):
        """ check that number does not exceed the limit

         There is a tolerance of 1. That is, if the number is only 1 above
         the limit we mark as it as allowed to fail
        """
        if self.even_number <= self.limit:
            return PASS
        elif self.even_number - self.limit == 1:
            return FAIL("within tolerance", allowed_to_fail=True)
        else:
            return FAIL("outside tolerance")

    @classmethod
    @data_validator
    def test_increasing(cls):
        """ check that the numbers are increasing """
        last_num = None
        for obj in cls.objects.order_by("pk"):
            if last_num and obj.even_number < last_num:
                return PASS
            last_num = obj.even_number
        else:
            return FAIL

    @classmethod
    @data_validator
    def test_cls_exception(cls):
        """ hits an exception """
        raise ValueError("a value error on a classmethod!")

    @data_validator
    def test_inst_exception(self):
        """ hits an exception """
        raise ValueError("a value error on a instancemethod!")
