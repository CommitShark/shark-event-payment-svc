from pydantic_settings import BaseSettings, SettingsConfigDict


class GenericSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    charge_req_key: str

    debug: bool


settings = GenericSettings()  # type:ignore
