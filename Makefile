PYTHON ?= python
PIP ?= pip

help:
	@echo "Available targets:"
	@echo "  make install        -> install runtime dependencies"
	@echo "  make install-dev    -> install development dependencies"
	@echo "  make diagnose       -> run the environment diagnostic"
	@echo "  make smoke          -> compile scripts to catch syntax errors"
	@echo "  make test           -> run pytest"
	@echo "  make format         -> format code with black"
	@echo "  make lint           -> run ruff lint checks"
	@echo "  make precommit      -> run pre-commit hooks on all files"

install:
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -r requirements.txt

install-dev:
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -r requirements-dev.txt

diagnose:
	$(PYTHON) scripts/diagnostics/check_craterslab_env.py

smoke:
	$(PYTHON) -m compileall main.py scripts toolkit

test:
	pytest -q

format:
	black scripts toolkit tests

lint:
	ruff check scripts toolkit tests

precommit:
	pre-commit run --all-files
