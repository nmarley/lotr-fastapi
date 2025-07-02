import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


@pytest.mark.integration
class TestIntegration:
    """Integration tests that require real API access"""

    def test_health_endpoint_works(self):
        """Test that health endpoint works without external dependencies"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_real_api_call_gandalf(self):
        """Test real API call with Gandalf (requires valid API key)"""
        pytest.skip("Integration test - run with pytest --integration")

    def test_real_api_call_invalid_character(self):
        """Test real API call with invalid character"""
        pytest.skip("Integration test - run with pytest --integration")
