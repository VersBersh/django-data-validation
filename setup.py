#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pathlib import Path
from setuptools import setup

DESCRIPTION = "A Django app to manage the validation of your data."

with (Path(__file__).parent / "deps/pip.base").open("r") as f:
    REQUIREMENTS = f.read().splitlines()

with (Path(__file__).parent / "README.rst").open("r") as f:
    LONG_DESCRIPTION = f.read()

setup(
    name="django-data-validation",
    version="0.0.1",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/x-rst",
    author="Oliver Chambers",
    author_email="django.data.validation@gmail.com",
    url="https://github.com/VersBersh/django-data-validation",
    packages=["datavalidation"],
    python_requires="~=3.6.0",
    install_requires=REQUIREMENTS,
    include_package_data=True,
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: Implementation :: CPython",
        "Framework :: Django :: 2.0",
    ],
)
