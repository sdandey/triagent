"""Web-specific configuration for Triagent API."""

from pydantic_settings import BaseSettings


class WebConfig(BaseSettings):
    """Web-specific configuration (loaded from environment)."""

    # Redis configuration
    redis_host: str = "localhost"
    redis_port: int = 6380
    redis_password: str = ""
    redis_ssl: bool = True

    # Azure Session Pool
    session_pool_endpoint: str = ""

    # Authentication
    triagent_api_key: str = ""  # Shared API key for backend auth

    # Session settings
    session_ttl: int = 7200  # 2 hours

    # CORS settings (comma-separated list of origins, or "*" for development)
    cors_origins: str = "*"

    model_config = {"env_prefix": "TRIAGENT_"}
