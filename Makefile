.PHONY: clean deps

clean:
	rm -fr build/
	rm -fr dist/
	rm -fr *.egg-info

lint:
	python -m flake8

test:
	(cd test_proj && python -m pytest)

build: clean
	python setup.py sdist
	python setup.py bdist_wheel

release: clean lint build
	python setup.py sdist upload
	python setup.py bdist_wheel upload

# combine pip.base and pip.dev into one (gitignoted) requirements file because pycharm
# can't handle two requirements files (n.b. $$ to escape $ in Make)
deps:
	cat ./deps/pip.base | sed -e 's/\n*$$//' > ./deps/pip.all
	cat ./deps/pip.dev | sed -e 's/^\n*//' >> ./deps/pip.all
