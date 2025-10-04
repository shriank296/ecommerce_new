# Makefile for building Docker Images

#Variables
DOCKERFILE=Dockerfile

install:
	poetry install --with dev

test:
	poetry run python -m pytest -vv tests

test-ci:
	poetry run python -m pytest -vv tests -m '' --cov=app --cov-report=term-missing --cov-report=xml:/tmp/coverage.xml

build:
	docker build -f $(DOCKERFILE) .

# Run all pre-commit hooks (linting, formatting, checks) on all files
lint:
	poetry run pre-commit run --all

# Generate or update the OpenAPI schema for the API
generate-openapi:
	poetry run scripts/update_api_definition.py generate

# Start the FastAPI application in development mode with auto-reload
start:
	poetry run uvicorn app.main:main --factory --reload --host=0.0.0.0 --port=8081	

# Generate a new Alembic migration based on current models
# Usage: make db_migrate MSG="Add new column to users table"
db_migrate:
	poetry run alembic revision --autogenerate -m "$(MSG)" 

# Apply all pending Alembic migrations to upgrade the database to the latest version
db_upgrade:
	poetry run alembic upgrade head

# Start all containers in the background
up:
	docker compose up -d

# Stop all containers
down:
	docker compose down

# Stop all containers and remove volumes
down-volumes:
	docker compose down -v
