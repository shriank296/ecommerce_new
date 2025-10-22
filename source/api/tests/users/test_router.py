import pytest
from fastapi.testclient import TestClient

from app.database import RootSession

test_data = {
    "first_name": "Kittu",
    "last_name": "Shrivastava",
    "email": "kitt@example.com",
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
    response = api_admin_client.post("/users", json=test_data)
    assert response.status_code == 201


@pytest.mark.integration
def test_create_user_customer_user(
    api_customer_client: TestClient, test_session: RootSession
):
    response = api_customer_client.post("/users", json=test_data)
    assert response.status_code == 403
