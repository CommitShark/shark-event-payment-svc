from pydantic_settings import BaseSettings, SettingsConfigDict


class GenericSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    charge_req_key: str

    account_validation_key: str

    debug: bool

    auto_withdrawal_enabled: int


settings = GenericSettings()  # type:ignore
