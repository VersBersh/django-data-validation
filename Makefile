.PHONY: clean

clean:
	rm -fr build/
	rm -fr dist/
	rm -fr *.egg-info

lint:
	python -m flake8

test:
	python -m pytest

build: clean
	python setup.py sdist
	python setup.py bdist_wheel

release: clean lint build
	python setup.py sdist upload
	python setup.py bdist_wheel upload

