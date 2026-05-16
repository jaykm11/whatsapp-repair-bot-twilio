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

    # Conversation memory: memory (default, single-process) or firestore (Cloud Run)
    conversation_backend: str = Field(
        default="memory",
        description='Conversation persistence: "memory" or "firestore"',
    )
    conversation_max_messages: int = Field(
        default=24,
        ge=4,
        le=200,
        description="Max stored messages per user (user + assistant turns).",
    )
    google_cloud_project: str = Field(
        default="",
        description="GCP project id for Firestore (optional; Cloud Run sets GOOGLE_CLOUD_PROJECT).",
    )

    # Vertex AI Memory Bank (optional; set on Cloud Run when Reasoning Engine exists)
    vertex_agent_engine_name: str = Field(
        default="",
        description="Full resource name: projects/.../locations/.../reasoningEngines/...",
    )
    google_cloud_region: str = Field(
        default="us-central1",
        description="Vertex AI region (must match Reasoning Engine location).",
    )

    # Server configuration — Cloud Run injects PORT=8080
    port: int = Field(default=8080, description="Server port")
    log_level: str = Field(default="INFO", description="Logging level")


settings = Settings()
