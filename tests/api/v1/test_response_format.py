from fastapi import status


def test_discovery_endpoint_format(client):
    """
    Test that the discovery endpoint returns the standard SuccessResponse envelope.
    """
    response = client.get("/v1/.well-known/jwks.json")

    # Check status code
    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    # Verify standard envelope keys
    assert "success" in data
    assert "data" in data
    assert "api_version" in data
    assert "timestamp" in data

    # Verify content
    assert data["success"] is True
    assert data["api_version"] == "v1"
    assert "keys" in data["data"]


def test_error_response_format(client):
    """
    Test that a protected endpoint returns the standard FailureResponse envelope on error.
    """
    # Accessing /me without a token should trigger a 401
    response = client.get("/v1/accounts/me")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    data = response.json()

    # Verify standard failure envelope keys
    assert data["success"] is False
    assert "error" in data
    assert "api_version" in data
    assert "timestamp" in data

    # Verify error details
    assert data["error"]["code"] == "UNAUTHORIZED"
    assert "message" in data["error"]


def test_validation_error_format(client):
    """
    Test that sending invalid data returns the standard Validation Error envelope.
    """
    # POSTing empty data to /register
    response = client.post("/v1/accounts/register", json={})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    data = response.json()

    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "details" in data["error"]
    assert isinstance(data["error"]["details"], list)
