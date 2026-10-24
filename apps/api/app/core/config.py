from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    PROJECT_NAME: str = "NeuroSyn Sentinel Twin"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DATABASE_URL: str = f"sqlite:///{ROOT_DIR / 'sentinel_twin.db'}"

    # Gemma 4 Provider Settings
    GEMMA_PROVIDER: str = "deterministic_fallback"
    GEMMA_MODEL_NAME: str = "gemma4:latest"
    GEMMA_API_BASE: str = "http://localhost:11434"
    GEMMA_API_KEY: str = ""

    # Docker Sandbox Settings
    DOCKER_SANDBOX_ENABLED: bool = True
    SANDBOX_TIMEOUT_SECONDS: int = 45

    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()