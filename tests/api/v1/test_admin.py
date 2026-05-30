from fastapi import status


class TestAdminAccountListing:
    """Tests focused on the administrative list and search views."""

    def test_list_with_pagination_meta(self, authenticated_client, assert_standard_response):
        auth_client = authenticated_client(email="admin_list_class@example.com")

        # Seed some data
        for i in range(2):
            auth_client.post("/v1/accounts/register", json={"email": f"list_{i}@test.com", "password": "password123"})

        response = auth_client.get("/v1/admin/?limit=1&offset=0")
        data = assert_standard_response(response)

        assert data["meta"]["pagination"]["limit"] == 1
        assert len(data["data"]) == 1
        assert "total" in data["meta"]["pagination"]


class TestAdminAccountLifecycle:
    """Tests focused on individual account management actions."""

    def test_suspension_and_activation_cycle(self, authenticated_client, assert_standard_response):
        auth_client = authenticated_client(email="admin_cycle_class@example.com")

        # 1. Create target
        reg_res = auth_client.post(
            "/v1/accounts/register", json={"email": "cycle@test.com", "password": "password123"}
        )
        target_id = reg_res.json()["data"]["id"]

        # 2. Suspend
        sus_res = auth_client.post(f"/v1/admin/{target_id}/suspend")
        assert sus_res.json()["data"]["is_active"] is False

        # 3. Activate
        act_res = auth_client.post(f"/v1/admin/{target_id}/activate")
        assert act_res.json()["data"]["is_active"] is True

    def test_deletion_integrity(self, authenticated_client, assert_standard_response):
        auth_client = authenticated_client(email="admin_delete_class@example.com")
        reg_res = auth_client.post(
            "/v1/accounts/register", json={"email": "kill_me@test.com", "password": "password123"}
        )
        target_id = reg_res.json()["data"]["id"]

        # Delete
        response = auth_client.delete(f"/v1/admin/{target_id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify 404
        get_res = auth_client.get(f"/v1/admin/{target_id}")
        assert_standard_response(get_res, status_code=status.HTTP_404_NOT_FOUND, success=False)

    def test_get_account_details(self, authenticated_client, assert_standard_response):
        auth_client = authenticated_client()
        reg_res = auth_client.post(
            "/v1/accounts/register", json={"email": "details@test.com", "password": "password123"}
        )
        target_id = reg_res.json()["data"]["id"]

        response = auth_client.get(f"/v1/admin/{target_id}")
        data = assert_standard_response(response)
        assert data["data"]["email"] == "details@test.com"
