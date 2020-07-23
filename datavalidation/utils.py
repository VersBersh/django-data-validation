from functools import wraps
import itertools
import sys
import time

import inspect
from typing import Callable, Type, Iterable, TypeVar, Tuple, List

from django.db import models
from django.db.models import prefetch_related_objects


T = TypeVar("T")


def is_class_method(method: Callable, owner: Type) -> bool:
    """ return True if a function is a classmethod """
    assert callable(method) and owner is not None
    return inspect.ismethod(method) and getattr(method, "__self__", None) is owner


def chunk(iterable: Iterable[T], size: int) -> Iterable[T]:
    """ iterate an iterable in chunks """
    it = iter(iterable)
    return iter(lambda: tuple(itertools.islice(it, size)), ())


def partition(iterable: Iterable[T], predicate: Callable) -> Tuple[List[T], List[T]]:
    """ partition a list into two depending on a predicate """
    trues, falses = [], []
    for element in iterable:
        trues.append(element) if predicate(element) else falses.append(element)
    return trues, falses


# noinspection PyProtectedMember
def queryset_iterator(queryset: models.QuerySet, chunk_size: int):
    """ QuerySet.iterate with prefetch_related

     QuerySet.iterate silently ignores prefetch_related
     modified from this PR: https://github.com/django/django/pull/10707/files
    """
    iterable = queryset._iterable_class(queryset, chunked_fetch=True, chunk_size=chunk_size)
    if not queryset._prefetch_related_lookups:
        yield from iterable
        return

    iterator = iter(iterable)
    while True:
        results = list(itertools.islice(iterator, chunk_size))
        if not results:
            break
        prefetch_related_objects(results, *queryset._prefetch_related_lookups)
        yield from iter(results)


def timer(output: Callable):
    """ decorator to record the execution time of a function """
    def wrapper(func: Callable) -> Callable:
        @wraps(func)
        def inner(*args, **kwargs):
            # quick and dirty, don't need precision timing
            start_time = time.time()
            ret = func(*args, **kwargs)
            seconds = time.time() - start_time
            hours, h = divmod(seconds, 60*60)
            minutes, seconds = divmod(h, 60)
            output(f"Total Execution Time: {hours:02.0f}h:{minutes:02.0f}m:{seconds:04.1f}s")
            return ret
        return inner
    return wrapper


def sysexit(func: Callable) -> Callable:
    """ use the function return value as the system exit code """
    @wraps(func)
    def wrapper(*args, **kwargs):
        sys.exit(func(*args, **kwargs))
    return wrapper
