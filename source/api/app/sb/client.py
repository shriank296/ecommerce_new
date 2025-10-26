import logging
import os
import uuid

from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from azure.servicebus import ServiceBusClient, ServiceBusMessage
from azure.servicebus.exceptions import ServiceBusError
from fastapi import Depends

from app.settings import AppSettings, get_app_settings
from app.users.schemas import UserCreated, UserCreatedHeaders, UserResult

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


def post_user_created_event(
    user_result: UserResult,
    client: ServiceBusClient,
):
    """Send a 'userCreated' event to the user-results-event topic.

    Env Vars expected:
        SB_ECOMMERCE_USER_CREATED_TOPIC - topic name
    """
    try:
        topic_name = os.getenv("SB_ECOMMERCE_USER_CREATED_TOPIC")
        if not topic_name:
            logger.warning(
                "SB_ECOMMERCE_USER_CREATED_TOPIC not set; skipping publish for user create"
            )
            return
        headers = UserCreatedHeaders(requestor_id=user_result.email)
        message_envelope = UserCreated(headers=headers, payload=user_result)

        with client.get_topic_sender(topic_name) as sender:
            event_message = ServiceBusMessage(
                message_envelope.payload.model_dump_json(by_alias=True),
                application_properties={
                    # replicate headers also as application properties for filtering
                    "eventType": message_envelope.headers.event_type,
                    "version": message_envelope.headers.version,
                    "requestorId": message_envelope.headers.requestor_id,
                },
                message_id=str(uuid.uuid4()),
                content_type=headers.content_type,
            )
            sender.send_messages(event_message)
            logger.info(
                "Sent 'UserCreated' event to topic %s with email=%s, phone=%s",
                topic_name,
                user_result.email,
                user_result.phone,
            )
    except ServiceBusError:
        logger.exception("Failed to send 'UserCreated' event.")
