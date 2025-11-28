from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class KafkaSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="KAFKA_",
        env_file=".env",
        extra="ignore",
    )

    bootstrap_servers: str
    group_id: str
    auto_offset_reset: Literal["earliest"] = "earliest"
    enable_auto_commit: bool = False


kafka_config = KafkaSettings()  # type: ignore
