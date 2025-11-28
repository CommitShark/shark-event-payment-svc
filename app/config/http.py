from pydantic_settings import BaseSettings, SettingsConfigDict


class HttpSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="HTTP_",
        env_file=".env",
        extra="ignore",
    )

    root_path: str = "/"

    allowed_origins: str = ""

    root_origin: str = ""


http_config = HttpSettings()
