import pytest
import httpx
from unittest.mock import patch, MagicMock
from services.the_one_api import TheOneAPIService, TheOneAPIError
from models.quotes import Character, Quote


@pytest.fixture
def mock_settings():
    """Mock settings with API key"""
    with patch("services.the_one_api.settings") as mock:
        mock.THE_ONE_API_KEY = "test-api-key"
        yield mock


@pytest.fixture
def api_service(mock_settings):
    """Create API service instance with mocked settings"""
    return TheOneAPIService()


@pytest.fixture
def sample_character_response():
    """Sample character API response"""
    return {
        "docs": [
            {
                "_id": "5cd99d4bde30eff6ebccfbbe",
                "height": "",
                "race": "Maiar",
                "gender": "Male",
                "birth": "",
                "spouse": "",
                "death": "",
                "realm": "",
                "hair": "",
                "name": "Gandalf",
                "wikiUrl": "http://lotr.wikia.com//wiki/Gandalf",
            }
        ],
        "total": 1,
        "limit": 1000,
        "offset": 0,
        "page": 1,
        "pages": 1,
    }


@pytest.fixture
def sample_quote_response():
    """Sample quote API response"""
    return {
        "docs": [
            {
                "_id": "5cd96e05de30eff6ebcce7e9",
                "dialog": "A wizard is never late, nor is he early, he arrives precisely when he means to.",
                "movie": "5cd95395de30eff6ebccde5b",
                "character": "5cd99d4bde30eff6ebccfbbe",
                "id": "5cd96e05de30eff6ebcce7e9",
            },
            {
                "_id": "5cd96e05de30eff6ebcce7ea",
                "dialog": "I am looking for someone to share in an adventure.",
                "movie": "5cd95395de30eff6ebccde5b",
                "character": "5cd99d4bde30eff6ebccfbbe",
                "id": "5cd96e05de30eff6ebcce7ea",
            },
        ],
        "total": 2,
        "limit": 1000,
        "offset": 0,
        "page": 1,
        "pages": 1,
    }


@pytest.fixture
def empty_response():
    """Empty API response"""
    return {"docs": [], "total": 0, "limit": 1000, "offset": 0, "page": 1, "pages": 1}


class TestTheOneAPIService:
    """Test suite for The One API service"""

    def test_service_initialization_success(self, mock_settings):
        """Test successful service initialization with API key"""
        service = TheOneAPIService()
        assert service.headers["Authorization"] == "Bearer test-api-key"
        assert service.headers["Accept"] == "application/json"

    def test_service_initialization_no_api_key(self):
        """Test service initialization fails without API key"""
        with patch("services.the_one_api.settings") as mock:
            mock.THE_ONE_API_KEY = None
            with pytest.raises(
                ValueError, match="THE_ONE_API_KEY is required but not set"
            ):
                TheOneAPIService()

    @pytest.mark.asyncio
    async def test_make_request_success(self, api_service, sample_character_response):
        """Test successful API request"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = sample_character_response
            mock_response.raise_for_status.return_value = None

            mock_client.return_value.__aenter__.return_value.get.return_value = (
                mock_response
            )

            result = await api_service._make_request("character")
            assert result == sample_character_response

    @pytest.mark.asyncio
    async def test_make_request_401_error(self, api_service):
        """Test API request with 401 authentication error"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 401
            error = httpx.HTTPStatusError(
                "Unauthorized", request=MagicMock(), response=mock_response
            )

            mock_client.return_value.__aenter__.return_value.get.side_effect = error

            with pytest.raises(TheOneAPIError) as exc_info:
                await api_service._make_request("character")

            assert exc_info.value.status_code == 401
            assert "Authentication failed" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_make_request_404_error(self, api_service):
        """Test API request with 404 not found error"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 404
            error = httpx.HTTPStatusError(
                "Not Found", request=MagicMock(), response=mock_response
            )

            mock_client.return_value.__aenter__.return_value.get.side_effect = error

            with pytest.raises(TheOneAPIError) as exc_info:
                await api_service._make_request("character")

            assert exc_info.value.status_code == 404
            assert "Resource not found" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_make_request_429_rate_limit(self, api_service):
        """Test API request with 429 rate limit error"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 429
            error = httpx.HTTPStatusError(
                "Too Many Requests", request=MagicMock(), response=mock_response
            )

            mock_client.return_value.__aenter__.return_value.get.side_effect = error

            with pytest.raises(TheOneAPIError) as exc_info:
                await api_service._make_request("character")

            assert exc_info.value.status_code == 429
            assert "Rate limit exceeded" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_make_request_connection_error(self, api_service):
        """Test API request with connection error"""
        with patch("httpx.AsyncClient") as mock_client:
            error = httpx.RequestError("Connection failed")
            mock_client.return_value.__aenter__.return_value.get.side_effect = error

            with pytest.raises(TheOneAPIError) as exc_info:
                await api_service._make_request("character")

            assert exc_info.value.status_code == 503
            assert "Failed to connect to The One API" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_search_character_by_name_exact_match(
        self, api_service, sample_character_response
    ):
        """Test character search with exact name match"""
        with patch.object(
            api_service, "_make_request", return_value=sample_character_response
        ):
            character = await api_service.search_character_by_name("Gandalf")

            assert character is not None
            assert character.name == "Gandalf"
            assert character.race == "Maiar"

    @pytest.mark.asyncio
    async def test_search_character_by_name_case_insensitive(
        self, api_service, sample_character_response
    ):
        """Test character search is case insensitive"""
        with patch.object(
            api_service, "_make_request", return_value=sample_character_response
        ):
            character = await api_service.search_character_by_name("gandalf")

            assert character is not None
            assert character.name == "Gandalf"

    @pytest.mark.asyncio
    async def test_search_character_by_name_not_found(
        self, api_service, empty_response
    ):
        """Test character search when character not found"""
        with patch.object(api_service, "_make_request", return_value=empty_response):
            character = await api_service.search_character_by_name(
                "NonExistentCharacter"
            )

            assert character is None

    @pytest.mark.asyncio
    async def test_get_character_quotes_success(
        self, api_service, sample_quote_response
    ):
        """Test successful quote retrieval for character"""
        with patch.object(
            api_service, "_make_request", return_value=sample_quote_response
        ):
            quotes = await api_service.get_character_quotes("5cd99d4bde30eff6ebccfbbe")

            assert len(quotes) == 2
            assert (
                quotes[0].dialog
                == "A wizard is never late, nor is he early, he arrives precisely when he means to."
            )

    @pytest.mark.asyncio
    async def test_get_random_character_quote_success(
        self, api_service, sample_character_response, sample_quote_response
    ):
        """Test successful random quote retrieval"""
        with (
            patch.object(api_service, "search_character_by_name") as mock_search,
            patch.object(api_service, "get_character_quotes") as mock_quotes,
            patch("random.choice") as mock_choice,
        ):
            character = Character(**sample_character_response["docs"][0])
            mock_search.return_value = character

            quotes = [Quote(**doc) for doc in sample_quote_response["docs"]]
            mock_quotes.return_value = quotes

            mock_choice.return_value = quotes[0]

            quote = await api_service.get_random_character_quote("Gandalf")

            assert quote is not None
            assert (
                quote.dialog
                == "A wizard is never late, nor is he early, he arrives precisely when he means to."
            )

    @pytest.mark.asyncio
    async def test_get_random_character_quote_character_not_found(self, api_service):
        """Test random quote when character not found"""
        with patch.object(api_service, "search_character_by_name", return_value=None):
            quote = await api_service.get_random_character_quote("NonExistentCharacter")

            assert quote is None
