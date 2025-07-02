"""
Lord of the Rings Quote API Service

A FastAPI service that provides random quotes from Lord of the Rings characters
using The One API (https://the-one-api.dev/).

This service offers:
- Character quote retrieval with case-insensitive character name matching
- Comprehensive error handling and logging
- Production-ready configuration management
- Full OpenAPI documentation

Author: FastAPI Service Team
Version: 1.0.0
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import logging

from routes import health, quotes
from settings import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Get settings for configuration
settings = get_settings()

# Initialize FastAPI application with comprehensive metadata
app = FastAPI(
    title="Lord of the Rings Quote API",
    description="""
    A FastAPI service that provides random quotes from Lord of the Rings characters.
    
    ## Features
    
    * **Character Quotes**: Get random quotes from your favorite LotR characters
    * **Case-Insensitive Search**: Character names work regardless of case
    * **Comprehensive Error Handling**: Detailed error responses for all scenarios
    * **Production Ready**: Full logging, monitoring, and configuration management
    
    ## Authentication
    
    This service uses The One API (https://the-one-api.dev/) which requires an API key.
    The API key must be configured via the `THE_ONE_API_KEY` environment variable.
    
    ## Rate Limits
    
    This service is subject to The One API's rate limits. If rate limits are exceeded,
    the service will return a 503 Service Unavailable response.
    
    ## Supported Characters
    
    The service supports all characters from The One API database, including but not limited to:
    - Gandalf
    - Frodo
    - Aragorn  
    - Legolas
    - Gimli
    - Boromir
    - And many more...
    """,
    version="1.0.0",
    contact={
        "name": "API Support",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_tags=[
        {
            "name": "quotes",
            "description": "Operations related to character quotes from Lord of the Rings",
        },
        {
            "name": "health",
            "description": "Service health and status checks",
        },
    ],
)

# Add CORS middleware for production readiness
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include routers with proper tags
app.include_router(health.router, tags=["health"])
app.include_router(quotes.router, tags=["quotes"])


@app.get("/", include_in_schema=False)
async def root():
    """
    Root endpoint that redirects to the API documentation.

    Returns:
        RedirectResponse: Redirect to the interactive API docs
    """
    return RedirectResponse(url="/docs")


@app.on_event("startup")
async def startup_event():
    """
    Application startup event handler.

    Performs initialization tasks and logs startup information.
    """
    logger.info(f"Starting {app.title} v{app.version}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")

    # Validate critical configuration
    if not settings.THE_ONE_API_KEY:
        logger.warning(
            "THE_ONE_API_KEY is not configured - API functionality will be limited"
        )
    else:
        logger.info("The One API key is configured")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown event handler.

    Performs cleanup tasks and logs shutdown information.
    """
    logger.info(f"Shutting down {app.title}")
