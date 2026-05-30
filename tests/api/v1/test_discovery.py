class TestDiscovery:
    """Tests for technical discovery endpoints (OIDC/JWKS)."""

    def test_jwks_standard_compliance(self, client, assert_standard_response):
        """Verify JWKS returns valid RSA keys in the IdentityX envelope."""
        response = client.get("/v1/.well-known/jwks.json")
        data = assert_standard_response(response)

        assert "keys" in data["data"]
        keys = data["data"]["keys"]
        assert len(keys) > 0

        # Verify first key structure
        key = keys[0]
        assert key["alg"] == "RS256"
        assert key["kty"] == "RSA"
        assert "kid" in key
