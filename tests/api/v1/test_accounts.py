import pytest
from fastapi import status


class TestAccountRegistration:
    """Tests related to the user registration process."""

    def test_success(self, client, assert_standard_response):
        response = client.post(
            "/v1/accounts/register", json={"email": "register_class@example.com", "password": "SecurePassword123!"}
        )
        data = assert_standard_response(response, status_code=status.HTTP_201_CREATED)
        assert data["data"]["email"] == "register_class@example.com"

    @pytest.mark.parametrize(
        "invalid_email",
        [
            "not-an-email",
            "missing@domain",
            "",
        ],
    )
    def test_invalid_email_format(self, client, assert_standard_response, invalid_email):
        response = client.post("/v1/accounts/register", json={"email": invalid_email, "password": "Password123!"})
        assert_standard_response(response, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, success=False)

    def test_duplicate_email_conflict(self, client, assert_standard_response):
        email = "duplicate_class@example.com"
        client.post("/v1/accounts/register", json={"email": email, "password": "password123"})

        response = client.post("/v1/accounts/register", json={"email": email, "password": "password123"})
        data = assert_standard_response(response, status_code=status.HTTP_409_CONFLICT, success=False)
        assert "already exists" in data["error"]["message"].lower()


class TestAccountAuthentication:
    """Tests related to Login, Logout, and Token management."""

    def test_login_success(self, client, assert_standard_response):
        email = "auth_class@example.com"
        password = "Password123!"
        client.post("/v1/accounts/register", json={"email": email, "password": password})

        response = client.post("/v1/accounts/login", data={"username": email, "password": password})
        data = assert_standard_response(response)
        assert "access_token" in data["data"]["tokens"]
        assert "refresh_token" in response.cookies

    def test_login_failure_invalid_credentials(self, client, assert_standard_response):
        email = "fail_auth@example.com"
        client.post("/v1/accounts/register", json={"email": email, "password": "CorrectPassword123!"})

        response = client.post("/v1/accounts/login", data={"username": email, "password": "WrongPassword"})
        assert_standard_response(response, status_code=status.HTTP_401_UNAUTHORIZED, success=False)


class TestAccountProfile:
    """Tests related to the user's own profile and security boundaries."""

    def test_get_me_success(self, authenticated_client, assert_standard_response):
        email = "profile_class@example.com"
        auth_client = authenticated_client(email=email)

        response = auth_client.get("/v1/accounts/me")
        data = assert_standard_response(response)
        assert data["data"]["email"] == email

    def test_unauthorized_access_to_me(self, client, assert_standard_response):
        response = client.get("/v1/accounts/me")
        data = assert_standard_response(response, status_code=status.HTTP_401_UNAUTHORIZED, success=False)
        assert data["error"]["code"] == "UNAUTHORIZED"

    def test_tampered_token_rejection(self, client, assert_standard_response):
        response = client.get("/v1/accounts/me", headers={"Authorization": "Bearer invalid.token.here"})
        assert_standard_response(response, status_code=status.HTTP_401_UNAUTHORIZED, success=False)
