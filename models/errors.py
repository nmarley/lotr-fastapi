from pydantic import BaseModel
from typing import Optional


class ErrorResponse(BaseModel):
    """Standard error response model"""

    error: str
    message: str
    status_code: int


class CharacterNotFoundError(BaseModel):
    """Error response for when a character is not found"""

    error: str = "Character not found"
    message: str
    character_name: str


class ExternalAPIError(BaseModel):
    """Error response for external API failures"""

    error: str = "External API error"
    message: str
    service: str = "The One API"
    details: Optional[str] = None
