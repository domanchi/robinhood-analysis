.PHONY: development
development: venv/bin/activate
	venv/bin/pip install -r requirements-dev-minimal.txt
	pre-commit install

venv/bin/activate:
	test -d venv || virtualenv venv
	venv/bin/pip install -r requirements-minimal.txt
	touch venv/bin/activate
