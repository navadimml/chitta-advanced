"""
Configuration management for Chitta backend
Loads settings from environment variables
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    app_name: str = "Chitta"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"

    # LLM Configuration
    llm_provider: str = "gemini"  # "gemini", "anthropic", or "openai"
    llm_model: Optional[str] = None

    # API Keys
    gemini_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None

    # Graphiti & Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"

    # CORS
    allowed_origins: str = "http://localhost:3000,http://localhost:5173"

    # JWT
    jwt_secret_key: str = "your-secret-key-change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # Storage
    storage_type: str = "local"  # or "s3"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_s3_bucket: Optional[str] = None
    aws_region: str = "us-east-1"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
