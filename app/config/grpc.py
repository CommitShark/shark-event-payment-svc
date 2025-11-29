from pydantic_settings import BaseSettings, SettingsConfigDict


class GrpcSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", env_prefix="GRPC_"
    )

    ticket_svc_target: str = "127.0.0.1:50051"


grpc_config = GrpcSettings()  # type:ignore
