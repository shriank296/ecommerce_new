# Makefile for building Docker Images

#Variables
DOCKERFILE=Dockerfile

install:
	poetry install --with dev

test:
	poetry run python -m pytest -vv tests

test-ci:
	poetry run python -m pytest -vv tests -m '' --cov=app --cov-report=term-missing --cov-report=xml:/tmp/

build:
	docker build -f $(DOCKERFILE) .

lint:
	poetry run pre-commit run --all

generate-openapi:
	poetry run scripts/update_api_definition.py generate

start:
	poetry run uvicorn app.main:main --factory --reload --host=0.0.0.0 --port=8081	

db_migrate:
	poetry run alembic revision --autogenerate -m "$(MSG)" 
