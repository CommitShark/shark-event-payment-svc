from pydantic_settings import BaseSettings, SettingsConfigDict


class PermifySettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="PERMIFY_",
        env_file=".env",
        extra="ignore",
    )

    url: str = ""
    tenant_id: str = ""


permify_config = PermifySettings()  # type: ignore
