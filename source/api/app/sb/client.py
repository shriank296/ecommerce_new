import logging

from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from azure.servicebus import ServiceBusClient
from fastapi import Depends

from app.settings import AppSettings, get_app_settings

logger = logging.getLogger(__name__)


def get_sb_client(
    app_settings: AppSettings = Depends(get_app_settings),
) -> ServiceBusClient:
    """Get a ServiceBusClient configured from the environment.
    Args:
        None
    Returns:
        ServiceBusClient
    """
    logger.debug("Setting up a new ServiceBusClient.")
    credential: ManagedIdentityCredential | DefaultAzureCredential
    # The environments outside of the local development env we need to use
    # managed identity to auth with the services.
    if app_settings.ENVIRONMENT not in ("local", "testing"):
        logger.debug("Using ManagedIdentityCredential")
        logger.debug("using connection Namespace %r", app_settings.SB_NAMESPACE)
        credential = ManagedIdentityCredential(client_id=app_settings.AZURE_CLIENT_ID)
        client = ServiceBusClient(
            app_settings.SB_NAMESPACE, credential, logging_enable=True
        )
    # We're running locally, just pipe in whatever is set in the namespace.
    else:
        logger.debug("Using DefaultCredential")
        logger.debug("Using connection %r", app_settings.SB_NAMESPACE)
        client = ServiceBusClient.from_connection_string(app_settings.SB_NAMESPACE)
    return client
