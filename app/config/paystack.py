from pydantic_settings import BaseSettings, SettingsConfigDict


class PaystackSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="PAYSTACK_",
        env_file=".env",
        extra="ignore",
    )

    url: str
    secret_key: str
    ticket_purchase_callback: str
    attendee_deposit_callback: str
    organizer_deposit_callback: str


paystack_config = PaystackSettings()  # type: ignore
