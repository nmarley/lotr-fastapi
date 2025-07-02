import pytest
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient
from fastapi import HTTPException

from main import app
from services.the_one_api import TheOneAPIError
from models.quotes import Character, Quote
from routes.quotes import get_the_one_api_service

client = TestClient(app)


@pytest.fixture
def sample_character():
    """Sample character object"""
    return Character(
        _id="5cd99d4bde30eff6ebccfbbe",
        height="",
        race="Maiar",
        gender="Male",
        birth="",
        spouse="",
        death="",
        realm="",
        hair="",
        name="Gandalf",
        wikiUrl="http://lotr.wikia.com//wiki/Gandalf",
    )


@pytest.fixture
def sample_quote():
    """Sample quote object"""
    return Quote(
        _id="5cd96e05de30eff6ebcce7e9",
        dialog="A wizard is never late, nor is he early, he arrives precisely when he means to.",
        movie="5cd95395de30eff6ebccde5b",
        character="5cd99d4bde30eff6ebccfbbe",
    )


@pytest.fixture(autouse=True)
def cleanup_dependency_overrides():
    """Ensure dependency overrides are cleaned up after each test"""
    yield
    app.dependency_overrides.clear()


class TestQuotesEndpoint:
    """Test suite for quotes endpoints"""

    def test_get_character_quote_success(self, sample_character, sample_quote):
        """Test successful quote retrieval"""
        mock_service = AsyncMock()
        mock_service.get_random_character_quote.return_value = sample_quote
        mock_service.search_character_by_name.return_value = sample_character

        app.dependency_overrides[get_the_one_api_service] = lambda: mock_service

        response = client.get("/quotes/gandalf")

        assert response.status_code == 200
        data = response.json()
        assert data["character"] == "Gandalf"
        assert (
            data["quote"]
            == "A wizard is never late, nor is he early, he arrives precisely when he means to."
        )
        assert data["movie"] == "5cd95395de30eff6ebccde5b"

    def test_get_character_quote_character_not_found(self):
        """Test quote retrieval when character not found"""
        mock_service = AsyncMock()
        mock_service.get_random_character_quote.return_value = None

        app.dependency_overrides[get_the_one_api_service] = lambda: mock_service

        response = client.get("/quotes/nonexistent")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_get_character_quote_case_insensitive(self, sample_character, sample_quote):
        """Test that character names are handled case-insensitively"""
        mock_service = AsyncMock()
        mock_service.get_random_character_quote.return_value = sample_quote
        mock_service.search_character_by_name.return_value = sample_character

        app.dependency_overrides[get_the_one_api_service] = lambda: mock_service

        # Test various case combinations
        for name in ["GANDALF", "gandalf", "GaNdAlF"]:
            response = client.get(f"/quotes/{name}")
            assert response.status_code == 200
            data = response.json()
            assert data["character"] == "Gandalf"

    def test_get_character_quote_api_auth_error(self):
        """Test API authentication error (401) returns 503"""
        mock_service = AsyncMock()
        mock_service.get_random_character_quote.side_effect = TheOneAPIError(
            "Authentication failed", 401
        )

        app.dependency_overrides[get_the_one_api_service] = lambda: mock_service

        response = client.get("/quotes/gandalf")

        assert response.status_code == 503
        data = response.json()
        assert "authentication failed" in data["detail"].lower()

    def test_get_character_quote_api_rate_limit(self):
        """Test API rate limit error (429) returns 503"""
        mock_service = AsyncMock()
        mock_service.get_random_character_quote.side_effect = TheOneAPIError(
            "Rate limit exceeded", 429
        )

        app.dependency_overrides[get_the_one_api_service] = lambda: mock_service

        response = client.get("/quotes/gandalf")

        assert response.status_code == 503
        data = response.json()
        assert "rate limit" in data["detail"].lower()

    def test_get_character_quote_api_not_found_error(self):
        """Test API 404 error returns 404"""
        mock_service = AsyncMock()
        mock_service.get_random_character_quote.side_effect = TheOneAPIError(
            "Resource not found", 404
        )

        app.dependency_overrides[get_the_one_api_service] = lambda: mock_service

        response = client.get("/quotes/gandalf")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_get_character_quote_api_other_error(self):
        """Test other API errors return the same status code"""
        mock_service = AsyncMock()
        mock_service.get_random_character_quote.side_effect = TheOneAPIError(
            "Bad Gateway", 502
        )

        app.dependency_overrides[get_the_one_api_service] = lambda: mock_service

        response = client.get("/quotes/gandalf")

        assert response.status_code == 502
        data = response.json()
        assert "The One API error" in data["detail"]

    def test_get_character_quote_unexpected_error(self):
        """Test unexpected errors return 500"""
        mock_service = AsyncMock()
        mock_service.get_random_character_quote.side_effect = ValueError(
            "Unexpected error"
        )

        app.dependency_overrides[get_the_one_api_service] = lambda: mock_service

        response = client.get("/quotes/gandalf")

        assert response.status_code == 500
        data = response.json()
        assert "unexpected error occurred" in data["detail"].lower()

    def test_get_character_quote_service_config_error(self):
        """Test service configuration error"""

        def mock_service_error():
            raise HTTPException(
                status_code=500, detail="The One API service is not properly configured"
            )

        app.dependency_overrides[get_the_one_api_service] = mock_service_error

        response = client.get("/quotes/gandalf")

        assert response.status_code == 500
        data = response.json()
        assert "not properly configured" in data["detail"]

    def test_get_character_quote_empty_character_name(self):
        """Test empty character name returns 404"""
        response = client.get("/quotes/")
        assert response.status_code == 404

    def test_get_character_quote_very_long_character_name(self):
        """Test very long character name"""
        mock_service = AsyncMock()
        mock_service.get_random_character_quote.return_value = None

        app.dependency_overrides[get_the_one_api_service] = lambda: mock_service

        long_name = "a" * 1000
        response = client.get(f"/quotes/{long_name}")
        assert response.status_code == 404

    def test_get_character_quote_response_format(self, sample_character, sample_quote):
        """Test response format matches expected schema"""
        mock_service = AsyncMock()
        mock_service.get_random_character_quote.return_value = sample_quote
        mock_service.search_character_by_name.return_value = sample_character

        app.dependency_overrides[get_the_one_api_service] = lambda: mock_service

        response = client.get("/quotes/gandalf")

        assert response.status_code == 200
        data = response.json()

        # Verify required fields
        assert "character" in data
        assert "quote" in data
        assert "movie" in data

        # Verify types
        assert isinstance(data["character"], str)
        assert isinstance(data["quote"], str)
        assert isinstance(data["movie"], str)

    def test_get_character_quote_fallback_character_name(self, sample_quote):
        """Test fallback when character search returns None but quote exists"""
        mock_service = AsyncMock()
        mock_service.get_random_character_quote.return_value = sample_quote
        mock_service.search_character_by_name.return_value = None

        app.dependency_overrides[get_the_one_api_service] = lambda: mock_service

        response = client.get("/quotes/gandalf")

        assert response.status_code == 200
        data = response.json()
        # Should use the requested character name as fallback
        assert data["character"] == "gandalf"

    def test_quotes_endpoint_in_openapi_docs(self):
        """Test that quotes endpoint appears in OpenAPI documentation"""
        response = client.get("/openapi.json")
        assert response.status_code == 200

        openapi_spec = response.json()
        paths = openapi_spec.get("paths", {})

        # Check that the quotes endpoint is documented
        assert "/quotes/{character_name}" in paths

        # Check the endpoint has proper documentation
        endpoint_spec = paths["/quotes/{character_name}"]
        assert "get" in endpoint_spec

        get_spec = endpoint_spec["get"]
        assert "summary" in get_spec
        assert "description" in get_spec
        assert "responses" in get_spec

        # Check documented response codes
        responses = get_spec["responses"]
        assert "200" in responses
        assert "404" in responses
        assert "503" in responses
        assert "500" in responses
