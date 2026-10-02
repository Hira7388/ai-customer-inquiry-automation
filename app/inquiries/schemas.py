from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class InquiryCreate(BaseModel):
    customer_id: UUID
    body: str = Field(min_length=1)
    idempotency_key: str = Field(min_length=1, max_length=128)

    @field_validator("body", "idempotency_key")
    @classmethod
    def reject_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Must not be blank")
        return value


class InquiryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    customer_id: UUID
    body: str
    status: str
    created_at: datetime
