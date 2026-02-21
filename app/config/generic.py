from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class GenericSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    charge_req_key: str

    account_validation_key: str

    auto_withdrawal_enabled: int

    settlement_delay_hours: int

    max_wallet_balance: int

    debug: bool = False

    @field_validator("debug", mode="before")
    def parse_debug(cls, v):
        if isinstance(v, str):
            return v.lower() in {"1", "true", "yes", "on"}
        return bool(v)


settings = GenericSettings()  # type:ignore
