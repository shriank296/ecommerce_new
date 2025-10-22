import json
import secrets
from pathlib import Path
from uuid import uuid4

from testcontainers.core.container import DockerContainer
from testcontainers.core.network import Network
from testcontainers.core.waiting_utils import wait_for_logs
from testcontainers.mssql import SqlServerContainer
from typing_extensions import Self

PASSWORD = secrets.token_urlsafe(32)
CONNECTION_STRING_FORMAT = (
    "Endpoint=sb://{}:{};SharedAccessKeyName=RootManageSharedAccessKey;"
    "SharedAccessKey=SAS_KEY_VALUE;UseDevelopmentEmulator=true;"
)
DEFAULT_IMAGE_NAME = "mcr.microsoft.com/azure-messaging/servicebus-emulator:latest"
DEFAULT_PORT = 5672


class AzureServiceBusEmulator(DockerContainer):
    def __init__(self, config: dict):
        super().__init__(DEFAULT_IMAGE_NAME)
        network = Network().create()
        sql_container = SqlServerContainer(
            "mcr.microsoft.com/mssql/server:2022-latest", password=PASSWORD
        )
        sql_container.with_env("ACCEPT_EULA", "Y")
        sql_container.with_env("SA_PASSWORD", "potatopotato1!")
        sql_container.with_network(network)
        sql_container.with_exposed_ports(1433)
        sql_container.with_network_aliases("sql")
        sql_container.start()
        # Create a temporary config file for the emulator
        tempdir = Path(f"/tmp/{uuid4()}")
        tempdir.mkdir()
        with open(str(Path(tempdir) / "Config.json"), "w") as f:
            f.write(json.dumps(config))
        self.with_volume_mapping(
            str(tempdir), "/ServiceBus_Emulator/ConfigFiles", mode="ro"
        ).with_env("SQL SERVER", "sql").with_env(
            "MSSQL_SA_PASSWORD", PASSWORD
        ).with_env(
            "ACCEPT_EULA", "Y"
        ).with_network_aliases(
            "servicebus"
        ).with_exposed_ports(
            DEFAULT_PORT
        ).with_network(
            network
        ).with_env(
            "SQL_WAIT_INTERNAL", "0"
        )

    def start(self) -> Self:
        super().start()
        wait_for_logs(self, "Emulator Services is successfully Up", timeout=300)
        return self

    def get_connection_string(self) -> str:
        host = self.get_container_host_ip()
        port = self.get_exposed_port(DEFAULT_PORT)
        return CONNECTION_STRING_FORMAT.format(host, port)
