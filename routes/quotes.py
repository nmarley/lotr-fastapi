"""
Quote API Routes

This module provides REST API endpoints for retrieving Lord of the Rings character quotes.
It integrates with The One API to fetch character data and quotes, providing a simplified
interface with comprehensive error handling.

The main endpoint allows clients to request random quotes from specific characters,
with case-insensitive character name matching and detailed error responses.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, Path

from services.the_one_api import TheOneAPIService, TheOneAPIError
from models.quotes import QuoteAPIResponse
from models.errors import ErrorResponse, ExternalAPIError
from settings import get_settings, BaseSettings

# Configure module-specific logger
logger = logging.getLogger(__name__)

# Create router instance
router = APIRouter(prefix="/quotes")


async def get_the_one_api_service(
    settings: BaseSettings = Depends(get_settings),
) -> TheOneAPIService:
    """
    Dependency injection for The One API service.

    This dependency provides a configured instance of TheOneAPIService
    with proper error handling for missing configuration.

    Args:
        settings: Application settings containing API configuration

    Returns:
        TheOneAPIService: Configured service instance

    Raises:
        HTTPException: 500 error if the service cannot be configured

    Example:
        ```python
        @router.get("/example")
        async def example_endpoint(
            api_service: TheOneAPIService = Depends(get_the_one_api_service)
        ):
            # Use api_service here
            pass
        ```
    """
    try:
        logger.debug("Creating The One API service instance")
        return TheOneAPIService()
    except ValueError as e:
        logger.error(f"Failed to create The One API service: {e}")
        raise HTTPException(
            status_code=500,
            detail="The One API service is not properly configured. Please check THE_ONE_API_KEY environment variable.",
        )


@router.get(
    "/{character_name}",
    response_model=QuoteAPIResponse,
    responses={
        200: {
            "description": "Successfully retrieved a random quote",
            "content": {
                "application/json": {
                    "example": {
                        "character": "Gandalf",
                        "quote": "A wizard is never late, nor is he early, he arrives precisely when he means to.",
                        "movie": "The Fellowship of the Ring",
                    }
                }
            },
        },
        404: {
            "model": ErrorResponse,
            "description": "Character not found or has no quotes",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Character 'UnknownCharacter' not found or has no quotes"
                    }
                }
            },
        },
        503: {
            "model": ExternalAPIError,
            "description": "External API unavailable or rate limited",
            "content": {
                "application/json": {
                    "example": {"detail": "The One API rate limit exceeded"}
                }
            },
        },
        500: {
            "model": ErrorResponse,
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {"detail": "An unexpected error occurred"}
                }
            },
        },
    },
    summary="Get Random Character Quote",
    description="""
    Retrieve a random quote from the specified Lord of the Rings character.
    
    This endpoint searches for the character by name (case-insensitive) and returns
    a random quote from their dialogue in the movies. The response includes the
    character's canonical name, the quote text, and the movie information.
    
    **Character Name Matching:**
    - Case-insensitive (e.g., "gandalf", "GANDALF", "Gandalf" all work)
    - Supports partial matching (e.g., "gand" may match "Gandalf")
    - Exact matches are preferred over partial matches
    
    **Supported Characters Include:**
    - Main Fellowship members (Frodo, Sam, Merry, Pippin, Gandalf, Aragorn, Boromir, Legolas, Gimli)
    - Other major characters (Saruman, Galadriel, Elrond, Théoden, Éowyn, Faramir, etc.)
    - Many minor characters with dialogue in the films
    
    **Rate Limiting:**
    This endpoint is subject to The One API's rate limits. If you receive a 503 error,
    please wait a moment before making additional requests.
    """,
    operation_id="get_character_quote",
)
async def get_character_quote(
    character_name: str = Path(
        ...,
        description="Name of the Lord of the Rings character (case-insensitive)",
        example="Gandalf",
        min_length=1,
        max_length=100,
    ),
    api_service: TheOneAPIService = Depends(get_the_one_api_service),
) -> QuoteAPIResponse:
    """
    Get a random quote from the specified Lord of the Rings character.

    This endpoint performs the following operations:
    1. Validates the character name input
    2. Searches for the character in The One API database
    3. Retrieves all quotes for the character
    4. Returns a random quote with character and movie information

    Args:
        character_name: The name of the character to get a quote from.
                       Case-insensitive, supports partial matching.
        api_service: Injected service for The One API operations

    Returns:
        QuoteAPIResponse: Object containing character name, quote text, and movie info

    Raises:
        HTTPException:
            - 404: Character not found or has no quotes
            - 503: External API unavailable, rate limited, or authentication failed
            - 500: Internal server error or unexpected failure

    Example:
        ```
        GET /quotes/gandalf

        Response:
        {
            "character": "Gandalf",
            "quote": "A wizard is never late, nor is he early, he arrives precisely when he means to.",
            "movie": "The Fellowship of the Ring"
        }
        ```
    """
    # Input validation and sanitization
    character_name_clean = character_name.strip()
    if not character_name_clean:
        logger.warning("Empty character name provided")
        raise HTTPException(status_code=400, detail="Character name cannot be empty")

    logger.info(f"Fetching quote for character: '{character_name_clean}'")

    try:
        # Attempt to get a random quote for the character
        quote = await api_service.get_random_character_quote(character_name_clean)

        if not quote:
            logger.info(f"No quotes found for character: '{character_name_clean}'")
            raise HTTPException(
                status_code=404,
                detail=f"Character '{character_name_clean}' not found or has no quotes",
            )

        # Get character info for the response (for canonical name)
        character = await api_service.search_character_by_name(character_name_clean)
        character_display_name = character.name if character else character_name_clean

        logger.info(f"Successfully retrieved quote for '{character_display_name}'")

        return QuoteAPIResponse(
            character=character_display_name, quote=quote.dialog, movie=quote.movie
        )

    except HTTPException:
        # Re-raise FastAPI HTTPExceptions as-is
        raise

    except TheOneAPIError as e:
        # Handle specific API errors with appropriate HTTP status codes
        logger.error(
            f"The One API error for '{character_name_clean}': {e.status_code} - {e.message}"
        )

        if e.status_code == 404:
            raise HTTPException(
                status_code=404, detail=f"Character '{character_name_clean}' not found"
            )
        elif e.status_code == 401:
            logger.error(
                "The One API authentication failed - check API key configuration"
            )
            raise HTTPException(
                status_code=503, detail="The One API authentication failed"
            )
        elif e.status_code == 429:
            logger.warning("The One API rate limit exceeded")
            raise HTTPException(
                status_code=503,
                detail="The One API rate limit exceeded. Please try again later.",
            )
        elif e.status_code == 503:
            logger.error("The One API is currently unavailable")
            raise HTTPException(
                status_code=503,
                detail="The One API is currently unavailable. Please try again later.",
            )
        else:
            # Proxy other HTTP status codes from the backend
            logger.error(f"Unexpected The One API error: {e.status_code} - {e.message}")
            raise HTTPException(
                status_code=e.status_code, detail=f"The One API error: {e.message}"
            )

    except Exception as e:
        # Handle any other unexpected errors
        logger.error(
            f"Unexpected error in get_character_quote for '{character_name_clean}': {type(e).__name__}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while processing your request",
        )
