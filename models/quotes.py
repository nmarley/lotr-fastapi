from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class Character(BaseModel):
    """Model for character data from The One API"""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(alias="_id")
    height: Optional[str] = None
    race: Optional[str] = None
    gender: Optional[str] = None
    birth: Optional[str] = None
    spouse: Optional[str] = None
    death: Optional[str] = None
    realm: Optional[str] = None
    hair: Optional[str] = None
    name: str
    wikiUrl: Optional[str] = None


class Quote(BaseModel):
    """Model for quote data from The One API"""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(alias="_id")
    dialog: Optional[str] = None
    movie: str
    character: str


class TheOneAPIResponse(BaseModel):
    """Generic response wrapper for The One API"""

    docs: List[dict]
    total: int
    limit: int
    offset: int
    page: int
    pages: int


class CharacterResponse(BaseModel):
    """Response wrapper for character data"""

    docs: List[Character]
    total: int
    limit: int
    offset: int
    page: int
    pages: int


class QuoteResponse(BaseModel):
    """Response wrapper for quote data"""

    docs: List[Quote]
    total: int
    limit: int
    offset: int
    page: int
    pages: int


class QuoteAPIResponse(BaseModel):
    """Our API response model for quote endpoints"""

    character: str
    quote: str
    movie: Optional[str] = None
