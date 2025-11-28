from urllib.parse import quote_plus
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SQLALCHEMY_",
        env_file=".env",
        extra="ignore",
    )

    url: str = Field(
        default="postgresql+asyncpg://localhost/defaultdb",
        examples=["postgresql+asyncpg://user:pass@host:5432/db"],
        description="Async PostgreSQL connection URL (asyncpg driver)",
    )

    url_sync: str = Field(
        default="postgresql+psycopg2://localhost/defaultdb",
        examples=["postgresql+psycopg2://user:pass@host:5432/db"],
        description="Sync PostgreSQL connection URL (psycopg2 driver)",
    )

    @field_validator("url", "url_sync", mode="before")
    def escape_special_chars(cls, v: str) -> str:
        """Automatically escape special characters in passwords"""
        if isinstance(v, str) and "@" in v:
            try:
                scheme, rest = v.split("://", 1)
                if "@" in rest:  # Has credentials
                    userinfo, hostport = rest.split("@", 1)
                    if ":" in userinfo:  # Has password
                        user, password = userinfo.split(":", 1)
                        return f"{scheme}://{user}:{quote_plus(password)}@{hostport}"
            except ValueError:
                pass
        return v


db_config = DatabaseSettings()  # type: ignore
