import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


@pytest.fixture
def integration_enabled(request):
    """Check if integration tests are enabled"""
    return request.config.getoption("--integration")


@pytest.mark.integration
class TestIntegration:
    """Integration tests that require real API access"""

    def test_health_endpoint_works(self):
        """Test that health endpoint works without external dependencies"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_real_api_call_gandalf(self, integration_enabled):
        """Test real API call with Gandalf (requires valid API key)"""
        if not integration_enabled:
            pytest.skip("Integration test - run with pytest --integration")

        response = client.get("/quotes/gandalf")

        # Should either succeed or fail gracefully
        if response.status_code == 200:
            data = response.json()
            assert "character" in data
            assert "quote" in data
            assert "movie" in data
            assert isinstance(data["character"], str)
            assert isinstance(data["quote"], str)
            assert len(data["quote"]) > 0
        elif response.status_code == 503:
            # API unavailable - acceptable for integration test
            data = response.json()
            assert "detail" in data
        else:
            pytest.fail(f"Unexpected status code: {response.status_code}")

    def test_real_api_call_invalid_character(self, integration_enabled):
        """Test real API call with invalid character"""
        if not integration_enabled:
            pytest.skip("Integration test - run with pytest --integration")

        response = client.get("/quotes/invalidcharacter123")

        # Should return 404 for invalid character
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
