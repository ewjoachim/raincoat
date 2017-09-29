.PHONY: help install clean clean-pyc clean-build docs tests acceptance-tests coverage lint docs release
.DEFAULT_GOAL := help

# Launch "make" or "make help" for details on every target
help:
	@python -c "import re; print(*sorted('\033[36m{:25}\033[0m {}'.format(*l.groups()) for l in re.finditer('(.+):.+##(.+)', open('Makefile').read())), sep='\n')"

install: ## install project dependencies
	pip install -r requirements.txt

# ------- Cleaning commands -------

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

# ------- Testing commands -------

tests: ## run tests quickly with the default Python
	pytest tests/

acceptance-tests: ## Launch acceptance tests (full integration tests without mocks)
	python acceptance_tests/test_full_chain.py

coverage: ## run tests quickly with the default Python
	pytest --cov --cov-report xml --cov-report term --cov-report html tests/

lint: ## check style with prospector
	prospector --with-tool pyroma

# ------- Other commands -------

docs: ## generate Sphinx HTML documentation, including API docs
	rm -f docs/raincoat.rst
	rm -f docs/modules.rst
	sphinx-apidoc -o docs/ raincoat
	$(MAKE) -C docs clean
	$(MAKE) -C docs html

release: clean ## package and upload a release
	fullrelease
