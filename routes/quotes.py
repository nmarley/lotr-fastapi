from fastapi import APIRouter, HTTPException, Depends
from services.the_one_api import TheOneAPIService, TheOneAPIError
from models.quotes import QuoteAPIResponse
from models.errors import ErrorResponse, ExternalAPIError
from settings import get_settings, BaseSettings

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
                detail=f"No quotes found for character '{character_name}'",
            )

        # Find character info for the response
        character = await api_service.search_character_by_name(character_name)
        character_display_name = character.name if character else character_name

        return QuoteAPIResponse(
            character=character_display_name, quote=quote.dialog, movie=quote.movie
        )

    except TheOneAPIError as e:
        if e.status_code == 404:
            raise HTTPException(
                status_code=404, detail=f"Character '{character_name}' not found"
            )
        elif e.status_code in [401, 429]:
            raise HTTPException(
                status_code=503, detail="The One API is currently unavailable"
            )
        else:
            raise HTTPException(status_code=503, detail="External API error occurred")
    except Exception:
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
