"""
Configuration management using Pydantic Settings
Loads environment variables from .env file
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Twilio credentials
    twilio_account_sid: str = Field(default="", description="Twilio Account SID")
    twilio_auth_token: str = Field(default="", description="Twilio Auth Token")
    twilio_whatsapp_number: str = Field(
        default="",
        description="Twilio WhatsApp sender number, e.g. whatsapp:+14155238886",
    )

    # Gemini AI credentials
    gemini_api_key: str = Field(default="", description="Google Gemini API key")

    # Server configuration — Cloud Run injects PORT=8080
    port: int = Field(default=8080, description="Server port")
    log_level: str = Field(default="INFO", description="Logging level")


settings = Settings()
