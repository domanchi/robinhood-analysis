.PHONY: development
development: venv/bin/activate
	venv/bin/pip install -r requirements-dev-minimal.txt
	pre-commit install

minimal: venv/bin/activate
venv/bin/activate:
	test -d venv || virtualenv venv
	venv/bin/pip install -r requirements-minimal.txt
	venv/bin/pip install -e .
	./scripts/initialize_database.py
	touch venv/bin/activate

clean:
	find . -type d -name __pycache__ -delete
	find . -type f -name *.pyc -delete
