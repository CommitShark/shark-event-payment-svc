from pydantic import BaseModel, Field, model_validator
from typing import Optional
from datetime import datetime, timezone
from uuid import UUID, uuid4

# === Entity ===


class ChargeSetting(BaseModel):
    """
    Aggregate root for charge settings.
    Lightweight entity that doesn't embed version history.
    Versions are managed through the repository.
    """

    charge_setting_id: UUID = Field(default_factory=uuid4)
    name: str = Field(description="Name/identifier for this charge setting")
    description: Optional[str] = Field(
        default=None, description="Description of what this charge is for"
    )
    charge_type: str = Field(description="Type of charge this setting represents")

    # Metadata
    created_at: datetime = Field(default_factory=lambda x: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda x: datetime.now(timezone.utc))
    is_active: bool = Field(
        default=True,
        description="Whether this charge setting is currently in use",
    )
