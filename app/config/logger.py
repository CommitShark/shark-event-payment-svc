import logging
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class LoggerSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="LOG_",
        env_file=".env",
        extra="ignore",
    )

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "DEBUG"
    to_file: bool = False
    file_path: str = "app.log"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    @property
    def logging_level(self) -> int:
        return getattr(logging, self.level.upper(), logging.DEBUG)


logging_config = LoggerSettings()
