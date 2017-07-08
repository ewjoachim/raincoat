.PHONY: clean-pyc clean-build docs help lint test test-all coverage release sdist acceptance-tests
.DEFAULT_GOAL := help

help:
	@perl -nle'print $& if m{^[a-zA-Z_-]+:.*?## .*$$}' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-25s\033[0m %s\n", $$1, $$2}'

install: ## install project dependencies
	pip install -r requirements.txt

clean: clean-build clean-pyc ## remove all artifacts
	rm -rf .tox/  # tox artifacts
	rm -rf .cache/  # pytest artifacts
	rm -rf htmlcov .coverage coverage.xml  # coverage artifacts

clean-build: ## remove build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -rf {} +

lint: ## check style with flake8
	flake8 --exclude=".tox,docs,build,tests/package/umbrella" .

test: ## run tests quickly with the default Python
	./runtests

acceptance-tests:
	pytest acceptance_tests/

test-all: ## run tests on every Python version with tox
	tox

coverage: ## check code coverage quickly with the default Python
	COVERAGE=1 ./runtests

docs: ## generate Sphinx HTML documentation, including API docs
	rm -f docs/raincoat.rst
	rm -f docs/modules.rst
	sphinx-apidoc -o docs/ raincoat
	$(MAKE) -C docs clean
	$(MAKE) -C docs html

release: clean ## package and upload a release
	fullrelease
