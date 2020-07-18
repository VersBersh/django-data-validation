.. _data_validators:

.. role:: sh(code)
    :language: bash

.. role:: py(code)
    :language: python


Writing Data Valiators
======================

There are two ways to write a data validator on a django model.

1. with a regular (instance) method
2. with a class method using the ``@classmethod`` decorator

An *instance method* should take one parameter (``self``) and return either:

- ``data_validator.PASS``, ``data_validator.FAIL``, ``data_validator.NA``, or
- A ``bool``

A *class method* should take one parameter (``cls``) and return either:

- ``data_validator.Summary``,
- ``data_validator.PASS``, ``data_validator.FAIL``,
- A ``QuerySet``, a ``list`` of model objects, or a ``list`` of model ids representing the objects that failed the validation, or
- A ``bool``


Examples
--------

For this section we will use the example models from the `django tutorial <https://docs.djangoproject.com/en/3.0/intro/tutorial02/>`_ of questions and their choices.

.. code-block:: python

    from django.db import models

    class Question(models.Model):
        question_text = models.CharField(max_length=200)
        pub_date = models.DateTimeField('date published')

    class Choice(models.Model):
        question = models.ForeignKey(Question, on_delete=models.CASCADE)
        choice_text = models.CharField(max_length=200)
        votes = models.IntegerField(default=0)

Suppose we want to validate that every question has exactly four choices, except those that were published before 2020 (when this criteria didn't apply). We can write a validator on the Question model.

.. code-block:: python

    from data_validation import data_validator, PASS, FAIL, NA
    from django.db import models

    class Quesiton(models.Model):
        ...
        @data_validator
        def check_four_choices_per_question(self):
            """ check that each question has exactly four choices

             <longer description if needed>
            """
            if self.pub_date.year < 2020:
                return NA("published before 2020")
            if self.choices.count() == 4:
                return PASS
            else:
                return FAIL

Some things to note:

- the short doc-string (i.e. up to the blank line) is read as the description for the data validator in the admin page
- ``PASS``, ``FAIL``, and ``NA`` can be returned with or without paraenthesis
- We cold have chosen to return ``True`` / ``False`` rather than ``PASS`` / ``FAIL``, but ``None`` cannot be used in place of ``NA``. This is to prevent code paths that do not explicitly return a value (possibly an error) being interpreted as ``NA``

You can also return a ``bool`` from a data validator, so we may write the above more succinctly as

.. code-block:: python

    @data_validator
    def check_four_choices_per_question(self):
        """ check that each question has exactly four choices """
        if self.pub_date.year < 2020:
            return NA("published before 2020")
        return self.choices.count() == 4


One significant problem with the above validator is that during validation it will be called for every object in the database table. This will be particularly slow because each object accessing ``self.choices`` requires a database query. Therefore ``data_validator`` supports two arguments: ``select_related`` and ``prefetch_related``, which may be a field name or a list of field names to select and prefetch respectively. see `here <https://docs.djangoproject.com/en/3.0/ref/models/querysets/#prefetch-related>`_. for more details about prefetch and select related.

The new validator looks like this

.. code-block:: python

    from data_validation import data_validator, PASS, FAIL, NA
    from django.db import models

    class Quesiton(models.Model):
        ...
        @data_validator(prefetch_related="choices")
        def check_four_choices_per_question(self):
            """ check that each question has exactly four choices """
            ...

This is a big improvement, but it still requires iterating over every object. To improve on this we can use a *class method validator*. In this way we can validate all of the objects with a single query

.. code-block:: python

    from data_validation import data_validator
    from django.db import models

    class Quesiton(models.Model):
        ...
        @classmethod
        @data_validator
        def check_four_choices_per_question(cls):
            """ check that each question has exactly four choices """
            return cls.objects \
                      .filter(pub_date__year__gte=2020) \
                      .annotate(choice_count=Count("choices")) \
                      .exclude(choice_count=4)


Things to note:

- select_related and prefetch_related have no effect when using a class method validator.
- we have returned a ``QuerySet`` of objects that fail the data validation. These will be saved to the database and you can review them in the admin page.

While the above validator is the most optimised, it doesn't provide the same detail of output as our first validator. Namely, the number of objects passing and NA are missing. Therefore, you have also the option to return a ``data_validator.Summary`` object that you can store these additional fields, which will make them available on the admin page (at the expense of two more database queryies).

.. code-block:: python

    from data_validation import data_validator, Summary
    from django.db import models

    class Quesiton(models.Model):
        ...
        @classmethod
        @data_validator
        def check_four_choices_per_question(cls):
            """ check that each question has exactly four choices """
            qs = cls.objects \
                    .filter(pub_date__year__gte=2020) \
                    .annotate(choice_count=Count("choices")) \
                    .exclude(choice_count=4)

            na_objects = cls.objects.filter(pub_date__year__lt=2020)
            passing_objects = qs.filter(choice_count=4)
            failing_objects = qs.exclude(choice_count=4)

            return Summary(
                num_na=na_objects.count()
                num_passing=passing_objects.count()
                failures=failing_objects  # no .count()!
            )
