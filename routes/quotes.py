import logging
from fastapi import APIRouter, HTTPException, Depends
from services.the_one_api import TheOneAPIService, TheOneAPIError
from models.quotes import QuoteAPIResponse
from models.errors import ErrorResponse, ExternalAPIError
from settings import get_settings, BaseSettings

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_the_one_api_service(
    settings: BaseSettings = Depends(get_settings),
) -> TheOneAPIService:
    """Dependency to get The One API service instance"""
    try:
        return TheOneAPIService()
    except ValueError:
        raise HTTPException(
            status_code=500, detail="The One API service is not properly configured"
        )


@router.get(
    "/quotes/{character_name}",
    response_model=QuoteAPIResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Character not found"},
        503: {"model": ExternalAPIError, "description": "External API unavailable"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Get a random quote from a character",
    description="Retrieve a random quote from the specified Lord of the Rings character",
)
async def get_character_quote(
    character_name: str,
    api_service: TheOneAPIService = Depends(get_the_one_api_service),
):
    """Get a random quote from the specified character"""
    try:
        quote = await api_service.get_random_character_quote(character_name)

        if not quote:
            raise HTTPException(
                status_code=404,
                detail=f"Character '{character_name}' not found or has no quotes",
            )

        # Find character info for the response
        character = await api_service.search_character_by_name(character_name)
        character_display_name = character.name if character else character_name

        return QuoteAPIResponse(
            character=character_display_name, quote=quote.dialog, movie=quote.movie
        )

    except HTTPException:
        # Let FastAPI HTTPExceptions bubble up naturally
        raise
    except TheOneAPIError as e:
        # Proxy the backend error status codes
        logger.error(
            f"TheOneAPIError for '{character_name}': {e.status_code} - {e.message}"
        )
        if e.status_code == 404:
            raise HTTPException(
                status_code=404, detail=f"Character '{character_name}' not found"
            )
        elif e.status_code == 401:
            raise HTTPException(
                status_code=503, detail="The One API authentication failed"
            )
        elif e.status_code == 429:
            raise HTTPException(
                status_code=503, detail="The One API rate limit exceeded"
            )
        else:
            # Proxy other HTTP status codes from the backend
            raise HTTPException(
                status_code=e.status_code, detail=f"The One API error: {e.message}"
            )
    except Exception as e:
        logger.error(
            f"Unexpected error in get_character_quote for '{character_name}': {type(e).__name__}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
