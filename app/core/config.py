from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"


class Settings(BaseSettings):
    whisper_model_name: str = "small"
    database_url: str
    celery_broker_url: str = "redis://redis:6379/0"

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def local_input_dir(self) -> Path:
        return DATA_DIR / "input"

    @property
    def local_output_dir(self) -> Path:
        return DATA_DIR / "output"

    @property
    def model_cache_dir(self) -> Path:
        return DATA_DIR / "models"

    def ensure_local_directories(self) -> None:
        for directory in (
            self.local_input_dir,
            self.local_output_dir,
            self.model_cache_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)


settings = Settings()
