from __future__ import annotations

import logging
import os
from collections.abc import Generator

import pytest
from azure.servicebus import ServiceBusClient
from faker import Faker
from fastapi import FastAPI
from fastapi.testclient import TestClient
from psycopg2 import connect
from psycopg2.extensions import connection
from sqlalchemy import text
from sqlalchemy.engine import Engine, create_engine
from testcontainers.postgres import PostgresContainer

from alembic import command, script
from alembic.config import Config
from app.common.security import get_current_user
from app.database.session import RootSession, get_database_session, get_engine
from app.main import main
from app.settings import (
    AppSettings,
    ExternalApiSettings,
    get_app_settings,
    get_external_api_settings,
)
from tests.helpers import build_postgres_dsn
from tests.sb.emulator import AzureServiceBusEmulator

logger = logging.getLogger(__name__)

# Service Bus configuration.

NAMESPACE = "sbemulatorns"
TOPIC = "test-topic"
SUBSCRIPTION = "test-subscription"
SB_CONFIG = {
    "UserConfig": {
        "Namespaces": [
            {
                "Name": NAMESPACE,
                "Queues": [],
                "Topics": [
                    {
                        "Name": TOPIC,
                        "Properties": {
                            "DefaultMessageTimeToLive": "PT1H",
                            "DuplicateDetecionHistoryTimeWindow": "PT20S",
                            "RequireDuplicateDetecion": False,
                        },
                        "Subscritptions": [
                            {
                                "Name": SUBSCRIPTION,
                                "Properties": {
                                    "DeadLetteringOnMessageExpiration": False,
                                    "DefaultMessageTimeToLive": "PT1H",
                                    "LockDuration": "PT1M",
                                    "MaxDeliveryCount": 10,
                                    "ForwardDeadLetteredMessagesTo": "",
                                    "ForwardTo": "",
                                    "RequireSession": False,
                                },
                                "Rules": [],
                            },
                        ],
                    }
                ],
            }
        ],
        "Logging": {"Type": "File"},
    }
}


@pytest.fixture(scope="session")
def postgresql() -> Generator[connection]:
    postgresql = PostgresContainer("postgres:16-alpine", dbname="test_db")
    postgresql.start()

    def load_database_from_models(db_connection: connection) -> None:
        """Create a test database from our alembic models."""
        print(f"db_connection: {db_connection.info.dsn_parameters}")
        dsn = build_postgres_dsn(
            password=postgresql.password, **db_connection.info.dsn_parameters
        )
        with db_connection.cursor():
            alembic_cfg = Config()
            alembic_cfg.set_main_option("script_location", "alembic")

            directory = script.ScriptDirectory.from_config(alembic_cfg)
            logger.debug("Current head is %r", directory.get_heads())

            # Overrwrite existing sqlalchemy URL with our own.
            alembic_cfg.set_main_option("sqlalchemy.url", dsn)
            # Given we start with an empty database we start at base.
            # Stamping this sets up the internal Alembic table that is used for
            # versioning in migrations.
            logger.debug("Stamping as current version.")
            command.stamp(alembic_cfg, "base")

            # Upgrade to head.
            command.upgrade(alembic_cfg, "head")

            db_connection.commit()

    db_connection = connect(
        dbname=postgresql.dbname,
        user=postgresql.username,
        password=postgresql.password,
        host=postgresql.get_container_host_ip(),
        port=postgresql.get_exposed_port(5432),
    )
    load_database_from_models(db_connection)
    yield db_connection


@pytest.fixture(scope="session")
def _db(postgresql: connection) -> Generator[Engine]:
    """Internal fixture used within the `conftest.py`.
    DO NOT USE THIS FIXTURE IN THE TESTS.
    """
    # params = postgresql.info.dsn_parameters

    # logger.debug(f"dsn is: {dsn}")

    # dsn = build_postgres_dsn(
    #     params["host"],
    #     params["port"],
    #     params["user"],
    #     params.get("password", ""),  # password might not always appear here
    #     params["dbname"],
    # )
    dsn = build_postgres_dsn(
        "127.0.0.1",
        str(postgresql.info.port),
        postgresql.info.user,
        postgresql.info.password,
        postgresql.info.dbname,
    )
    engine = create_engine(
        dsn,
        future=True,
        pool_size=80,
        max_overflow=0,
        pool_recycle=10,
        pool_timeout=5,
    )
    yield engine

    engine.dispose()


@pytest.fixture(scope="session")
def servicebus() -> Generator[AzureServiceBusEmulator]:
    sb = AzureServiceBusEmulator(config=SB_CONFIG)
    sb.start()
    yield sb


@pytest.fixture(scope="session")
def _sb(servicebus: AzureServiceBusEmulator) -> ServiceBusClient:
    conn_str = servicebus.get_connection_string()
    client = ServiceBusClient.from_connection_string(conn_str, logging_enable=True)
    return client


@pytest.fixture(scope="session")
def _app(_db: Engine, test_session: RootSession) -> FastAPI:
    """Internal fixture used within the `conftest.py`.

    DO NOT USE THIS FIXTURE IN THE TESTS.

    This is a palceholder fucntion that should have all of yout upstream
    dependencies as args. This enables ALL of the app to be ready before
    returning a full fastapi app for downstream use. This is session scoped
    so only needs to be setup once. We do this to keep setup complexity within
    `tests/conftest.py` rather than letting it spread into the tests.
    """

    # This is here to rewrite the lazy session handlers everywhere.
    assert test_session.execute(text("select 1 + 1")).scalars().one() == 2

    os.environ["ENVIRONMENT"] = "testing"

    app = main()
    return app


@pytest.fixture(scope="session")
def app(_app: FastAPI) -> FastAPI:
    return _app


@pytest.fixture(scope="session")
def dev_settings_override(postgresql: connection) -> AppSettings:
    """Override config to use test runner defined config over local env."""
    return AppSettings(
        SERVER_API_DOMAIN="http://test.brit.internal",
        ENVIRONMENT="testing",
        RELEASE="development",
        DB_NAME=postgresql.info.user,
        DB_USER=postgresql.info.password,
        DB_PASSWORD=postgresql.info.dbname,
        DB_HOST="localhost",
        DB_PORT=str(postgresql.info.port),
        AZURE_CLIENT_ID="ID",
        SB_NAMESPACE=NAMESPACE,
        SB_TOPIC=TOPIC,
        SB_SUBSCRIPTION=SUBSCRIPTION,
    )


@pytest.fixture(scope="session")
def external_settings_override() -> ExternalApiSettings:
    """Override config to use runner defined config over local env."""
    return ExternalApiSettings(EXTERNAL_API_SECRET="potatoes")


@pytest.fixture(scope="function")
def _api_client_base(
    _app: FastAPI,
    _db: Engine,
    # _sb: ServiceBusClient,
    dev_settings_override: AppSettings,
    external_settings_override: ExternalApiSettings,
) -> TestClient:
    """Function scoped test c;ient that returns a new client each call."""

    client = TestClient(_app, base_url=dev_settings_override.SERVER_API_DOMAIN)

    client.app.dependency_overrides[get_app_settings] = lambda: dev_settings_override
    client.app.dependency_overrides[get_external_api_settings] = (
        lambda: external_settings_override
    )
    client.app.dependency_overrides[get_engine] = lambda: _db
    # client.app.dependency_overrides[get_sb_client] = lambda: _sb

    return client


@pytest.fixture(scope="function")
def api_admin_client(_api_client_base, admin_user):
    _api_client_base.app.dependency_overrides[get_current_user] = lambda: admin_user
    return _api_client_base


@pytest.fixture(scope="function")
def api_customer_client(_api_client_base, customer_user):
    _api_client_base.app.dependency_overrides[get_current_user] = lambda: customer_user
    return _api_client_base


@pytest.fixture(scope="function")
def admin_user():
    return {"user_name": "test_user", "role": "ADMIN"}


@pytest.fixture(scope="function")
def customer_user():
    return {"user_name": "test_user", "role": "CUSTOMER"}


@pytest.fixture(scope="session")
def test_session(_db: Engine) -> RootSession:
    """Function scoped DB object that returns a new session call."""
    # Set the session on the lazy session handler.
    # This has to be here to link the factories which are within module
    # scope to the local test session which comes from the pytset
    # fixtures (e.g. postgresql)
    from tests.fixtures import lazy_session

    session = get_database_session(_db)
    lazy_session.override(session)

    return session


@pytest.fixture(scope="session")
def test_sb_client(_sb: ServiceBusClient) -> ServiceBusClient:
    """Session scoped service bus client."""
    return _sb


@pytest.fixture(scope="session")
def faker() -> Faker:
    return Faker()


# Import our other fixtures.
pytest_plugins = ["tests.users.fixtures"]
