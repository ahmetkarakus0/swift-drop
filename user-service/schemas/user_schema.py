import uuid
from datetime import datetime
from typing import Optional

from pydantic import AliasPath, BaseModel, ConfigDict, Field

from models import UserRole


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime


class MeResponse(UserResponse):
    # Let other services resolve the caller's role profile without a second request.
    customer_id: Optional[uuid.UUID] = Field(default=None, validation_alias=AliasPath("customer", "id"))
    courier_id: Optional[uuid.UUID] = Field(default=None, validation_alias=AliasPath("courier", "id"))
    merchant_id: Optional[uuid.UUID] = Field(default=None, validation_alias=AliasPath("merchant", "id"))
