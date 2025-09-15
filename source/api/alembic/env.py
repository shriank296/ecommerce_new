from logging.config import fileConfig
from typing import Literal

from pydantic_settings import BaseSettings
from sqlalchemy import engine_from_config, pool

from alembic import context
from app.database.base import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


class DatabaseConnection(BaseSettings):
    DB_USER: str
    DB_HOST: str
    DB_NAME: str
    AZURE_CLIENT_ID: str
    DB_PASSWORD: str | None = None
    DB_PORT: str = "5432"
    ENVIRONMENT: Literal["local", "testing", "dev", "tst", "uat", "prd"]


def get_db_settings() -> DatabaseConnection:
    return DatabaseConnection()


# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    db_settings = get_db_settings()

    if db_settings.ENVIRONMENT not in ("local", "testing"):
        pass
    else:
        connection_string = (
            f"postgresql://{db_settings.DB_USER}:{db_settings.DB_PASSWORD}"
            f"@{db_settings.DB_HOST}:{db_settings.DB_PORT}/{db_settings.DB_NAME}"
        )
    # url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=connection_string,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    def get_database_uri() -> str:
        db_settings = get_db_settings()

        connection_string = (
            f"postgresql://{db_settings.DB_USER}:{db_settings.DB_PASSWORD}"
            f"@{db_settings.DB_HOST}:{db_settings.DB_PORT}/{db_settings.DB_NAME}"
        )
        return (
            connection_string + "?sslmode=require"
            if db_settings.ENVIRONMENT not in ("local", "testing")
            else connection_string
        )

    configuration = config.get_section(config.config_ini_section)
    # If there's a pre-exisiting sqlalchemy URL configured then use that.
    # This is likely to happen in testing. If one doesn't exist then
    # We're probably in an environment to check the configuration.
    if not configuration.get("sqlalchemy.url"):
        configuration["sqlalchemy.url"] = get_database_uri()
    # This roundabout way of getting the URL is to allow for
    # the testing to override the URL with a different one.
    # This is done in the pytest_alembic runner.
    # https://pytest-alembic.readthedocs.io/en/stable/setup.html#env-py
    connectable = context.config.attributes.get("connection", None)
    if connectable is None:
        connectable = engine_from_config(
            configuration,
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
            echo=True,
        )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata, compare_type=True
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
