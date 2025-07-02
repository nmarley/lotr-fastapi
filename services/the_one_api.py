import httpx
import random
from typing import Optional, List

# from fastapi import HTTPException
from models.quotes import Character, Quote, CharacterResponse, QuoteResponse
from settings import get_settings

settings = get_settings()


class TheOneAPIError(Exception):
    """Custom exception for The One API errors"""

    def __init__(
        self, message: str, status_code: int = 500, details: Optional[str] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)


class TheOneAPIService:
    """Service class for interacting with The One API"""

    BASE_URL = "https://the-one-api.dev/v2"

    def __init__(self):
        if not settings.THE_ONE_API_KEY:
            raise ValueError("THE_ONE_API_KEY is required but not set")

        self.headers = {
            "Authorization": f"Bearer {settings.THE_ONE_API_KEY}",
            "Accept": "application/json",
        }

    async def _make_request(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """Make an authenticated request to The One API"""
        url = f"{self.BASE_URL}/{endpoint}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    url, headers=self.headers, params=params or {}
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    raise TheOneAPIError(
                        "Authentication failed. Please check your API key.",
                        status_code=401,
                    )
                elif e.response.status_code == 404:
                    raise TheOneAPIError("Resource not found", status_code=404)
                elif e.response.status_code == 429:
                    raise TheOneAPIError(
                        "Rate limit exceeded. Please try again later.", status_code=429
                    )
                else:
                    raise TheOneAPIError(
                        f"API request failed: {e.response.status_code}",
                        status_code=e.response.status_code,
                        details=str(e),
                    )
            except httpx.RequestError as e:
                raise TheOneAPIError(
                    "Failed to connect to The One API", status_code=503, details=str(e)
                )

    async def search_character_by_name(
        self, character_name: str
    ) -> Optional[Character]:
        """Search for a character by name (case-insensitive)"""
        try:
            # The One API supports regex matching, so we can do case-insensitive search
            params = {
                "name": f"/{character_name}/i"  # Case-insensitive regex
            }

            data = await self._make_request("character", params)
            response = CharacterResponse(**data)

            if not response.docs:
                return None

            # Find exact match first, then partial match
            exact_match = None
            partial_match = None

            for character in response.docs:
                if character.name.lower() == character_name.lower():
                    exact_match = character
                    break
                elif character_name.lower() in character.name.lower():
                    partial_match = character

            return exact_match or partial_match

        except TheOneAPIError:
            raise
        except Exception as e:
            raise TheOneAPIError(
                "Failed to search for character", status_code=500, details=str(e)
            )

    async def get_character_quotes(self, character_id: str) -> List[Quote]:
        """Get all quotes for a specific character"""
        try:
            endpoint = f"character/{character_id}/quote"
            data = await self._make_request(endpoint)
            response = QuoteResponse(**data)
            # Filter out quotes with None dialog
            return [quote for quote in response.docs if quote.dialog is not None]

        except TheOneAPIError:
            raise
        except Exception as e:
            raise TheOneAPIError(
                "Failed to fetch character quotes", status_code=500, details=str(e)
            )

    async def get_random_character_quote(self, character_name: str) -> Optional[Quote]:
        """Get a random quote from a character"""
        try:
            # First, find the character
            character = await self.search_character_by_name(character_name)
            if not character:
                return None

            # Get all quotes for the character
            quotes = await self.get_character_quotes(character.id)
            if not quotes:
                return None

            # Return a random quote
            return random.choice(quotes)

        except TheOneAPIError:
            raise
        except Exception as e:
            raise TheOneAPIError(
                "Failed to get random character quote", status_code=500, details=str(e)
            )
