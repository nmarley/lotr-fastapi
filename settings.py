import os
from enum import Enum
from functools import lru_cache

# Use pydantic_settings for better validation and type hints
from pydantic_settings import BaseSettings as PydanticBaseSettings


class AppSettings(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


# Still read ENVIRONMENT directly to decide which settings class to load
ENVIRONMENT = os.environ.get("ENVIRONMENT", AppSettings.DEVELOPMENT.value)


class BaseSettings(PydanticBaseSettings):
    """
    Base settings class using pydantic-settings.
    Settings are automatically loaded from environment variables.
    """

    APP_NAME: str = "FastAPI Service"
    DEBUG: bool = False
    ENVIRONMENT: str = ENVIRONMENT
    TESTING: bool = False

    # Pydantic-settings loads these from env vars automatically
    # Default to None if it must be provided
    DATABASE_URL: str | None = None
    SECRET_KEY: str | None = None

    # CORS settings - can still be overridden
    CORS_ORIGINS: list[str] = ["*"]

    # Add other common base settings here
    # pydantic-settings automatically loads this from the EXAMPLE_API_KEY environment variable.
    # It's optional (str | None) here, so it defaults to None if the env var isn't set.
    # If you defined it as `EXAMPLE_API_KEY: str`, pydantic would raise an error if the env var is missing.
    EXAMPLE_API_KEY: str | None = None

    # The One API key for accessing LotR data
    THE_ONE_API_KEY: str | None = None

    class Config:
        # Optional: Load settings from a .env file
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra env vars not defined in the model


class DevelopmentSettings(BaseSettings):
    """
    Development specific settings.
    Overrides defaults from BaseSettings.
    """

    DEBUG: bool = True
    # Provide defaults for development if env vars aren't set
    DATABASE_URL: str = "postgresql+psycopg2://user:password@localhost:5432/app_dev"
    SECRET_KEY: str = "a-very-insecure-development-secret-key"  # Change this!
    # e.g., CORS_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]


class StagingSettings(BaseSettings):
    """
    Staging specific settings.
    Requires DATABASE_URL and SECRET_KEY to be set via environment variables.
    """

    DEBUG: bool = False
    # No defaults - these must be provided in the staging environment
    DATABASE_URL: str
    SECRET_KEY: str


class ProductionSettings(BaseSettings):
    """
    Production specific settings.
    Requires DATABASE_URL and SECRET_KEY to be set via environment variables.
    Restricts CORS_ORIGINS.
    """

    DEBUG: bool = False
    # No defaults - these must be provided in the production environment
    DATABASE_URL: str
    SECRET_KEY: str
    CORS_ORIGINS: list[str] = ["https://your-production-domain.com"]


class TestingSettings(BaseSettings):
    """
    Testing specific settings.
    """

    TESTING: bool = True
    DEBUG: bool = True  # Often useful for debugging tests
    # Provide defaults for testing
    DATABASE_URL: str = "postgresql+psycopg2://user:password@localhost:5432/app_test"
    SECRET_KEY: str = "a-very-insecure-testing-secret-key"


@lru_cache()  # Cache the settings object for performance
def get_settings() -> BaseSettings:
    """
    Returns the settings object based on the ENVIRONMENT variable.
    Uses lru_cache to only instantiate the settings once.
    """
    env = ENVIRONMENT.lower()
    print(f"Loading settings for environment: {env}")
    if env == AppSettings.DEVELOPMENT.value:
        return DevelopmentSettings()
    elif env == AppSettings.STAGING.value:
        return StagingSettings()
    elif env == AppSettings.PRODUCTION.value:
        return ProductionSettings()
    elif env == AppSettings.TESTING.value:
        return TestingSettings()
    else:
        print(f"Warning: Unknown environment '{env}'. Falling back to BaseSettings.")
        # Fallback or raise an error depending on desired behavior
        return BaseSettings()


settings = get_settings()

# Example usage of the settings
print(f"App Name: {settings.APP_NAME}")
print(f"Environment: {settings.ENVIRONMENT}")
print(f"Database URL: {settings.DATABASE_URL}")
print(f"Secret Key: {settings.SECRET_KEY}")
print(f"CORS Origins: {settings.CORS_ORIGINS}")
print(f"Testing: {settings.TESTING}")
# Accessing the example setting
print(f"Example API Key: {settings.EXAMPLE_API_KEY}")
print(f"The One API Key: {settings.THE_ONE_API_KEY}")
