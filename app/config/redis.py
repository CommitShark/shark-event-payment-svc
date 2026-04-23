from pydantic_settings import BaseSettings, SettingsConfigDict


class RedisSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        env_prefix="REDIS_",
    )

    host: str = "localhost"
    db: int = 0
    port: int = 6379
    password: str | None = None


redis_config = RedisSettings()
