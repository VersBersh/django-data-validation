from datetime import date, timedelta

from numpy.random import randint, seed

from .models import TestModel


seed(1234)


def random_test_model_x():
    pass


def random_test_model(bad_even: bool = False,
                      bad_dates: bool = False,
                      bad_limit: bool = False
                      ) -> TestModel:

    """ generate some random data for TestModel """
    even = randint(1, 50) * 2
    if bad_even:
        even + 1

    start = date(2020, randint(1, 12), randint(1, 28))
    end = start + timedelta(days=randint(1, 30))
    if bad_dates:
        start, end = end, start

    if bad_limit:
        limit = even - 1
    else:
        limit = even * 2

    return TestModel.objects.create(
        even_number=even,
        start_date=start,
        end_date=end,
        limit=limit,
    )


def populate_data():
    for _ in range(1000):
        random_test_model_x()

    for _ in range(100):
        random_test_model()
    for _ in range(5):
        random_test_model(bad_even=True)
    for _ in range(5):
        random_test_model(bad_dates=True)
    for _ in range(5):
        random_test_model(bad_limit=True)
    for _ in range(5):
        random_test_model(bad_even=True, bad_dates=True, bad_limit=True)

