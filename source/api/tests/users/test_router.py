import json
from unittest.mock import patch

import pytest
from azure.servicebus import ServiceBusClient
from fastapi.testclient import TestClient

from app.database import RootSession
from tests.conftest import SUBSCRIPTION, TOPIC

test_data = {
    "first_name": "Kittu",
    "last_name": "Shrivastava",
    "email": "kittu@example.com",
    "phone": "9015",
    "address": {"street": "postal park"},
    "role": "ADMIN",
    "created_by": "Ankur",
    "updated_by": "Ankur",
    "_password": "kittu@123",
}


@pytest.mark.integration
def test_create_user_admin_user(
    api_admin_client: TestClient, test_session: RootSession
):
    with patch("app.users.router.post_user_created_event") as mock_sb:
        response = api_admin_client.post("/users", json=test_data)
        assert response.status_code == 201, response.text
        mock_sb.assert_called_once()
        call_args, call_kwargs = mock_sb.call_args
        event = call_args[0]
        assert event.email == "kittu@example.com"
        assert "client" in call_kwargs
        assert call_kwargs["client"] is not None


@pytest.mark.integration
def test_create_user_customer_user(
    api_customer_client: TestClient, test_session: RootSession
):
    with patch("app.users.router.post_user_created_event") as _:
        response = api_customer_client.post("/users", json=test_data)
        assert response.status_code == 403


@pytest.mark.integration
def test_user_created_event_published(
    api_admin_client: TestClient, _sb: ServiceBusClient
):
    """
    Verify that creating a user sends a 'UserCreated' event to the Service Bus topic.
    """

    # Arrange — input payload
    payload = {
        "first_name": "Kittu",
        "last_name": "Shrivastava",
        "email": "kit@exp.com",
        "phone": "9015",
        "address": {"street": "postal park"},
        "role": "ADMIN",
        "created_by": "Ankur",
        "updated_by": "Ankur",
        "_password": "kittu@123",
    }
    # Purge old messages
    # receiver = _sb.get_subscription_receiver(topic_name=TOPIC, subscription_name=SUBSCRIPTION)
    # with receiver:
    #     old_msgs = receiver.receive_messages(max_wait_time=3)
    #     for msg in old_msgs:
    #         receiver.complete_message(msg)
    #     if old_msgs:
    #         print(f"Purged {len(old_msgs)} stale messages before running the test.")

    # Act — call /users endpoint
    response = api_admin_client.post("/users", json=payload)
    assert response.status_code == 201, response.text
    created_user = response.json()
    assert created_user["email"] == payload["email"]

    # Assert — check Service Bus subscription for the event
    receiver = _sb.get_subscription_receiver(
        topic_name=TOPIC, subscription_name=SUBSCRIPTION
    )

    with receiver:
        messages = receiver.receive_messages(max_wait_time=10)
        assert len(messages) >= 1, "No Service Bus message received."

        found = False

        for msg in messages:
            body_bytes = b"".join([b for b in msg.body])
            body_str = body_bytes.decode("utf-8")

            try:
                body = json.loads(body_str)
            except json.JSONDecodeError:
                body = body_str  # just in case body isn't JSON

            app_props = {
                k.decode("utf-8") if isinstance(k, bytes) else k: (
                    v.decode("utf-8") if isinstance(v, bytes) else v
                )
                for k, v in (msg.application_properties or {}).items()
            }

            print("\n--- Message received ---")
            print("Body (raw):", body_str)
            print("Body (parsed):", body)
            print("Application Properties:", app_props)
            print("------------------------\n")

            if isinstance(body, dict) and body.get("email") == payload["email"]:
                found = True
                receiver.complete_message(msg)
                break
            else:
                receiver.complete_message(msg)

    assert found, f"Expected UserCreated event for {payload['email']} not found."
