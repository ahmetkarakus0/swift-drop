import enum
import uuid
from typing import Optional

from pydantic import BaseModel


class UserRole(str, enum.Enum):
    CUSTOMER = "customer"
    COURIER = "courier"
    MERCHANT = "merchant"
    ADMIN = "admin"


class CurrentUser(BaseModel):
    """Subset of user-service's GET /api/auth/me response."""

    id: uuid.UUID
    role: UserRole
    is_active: bool
    is_verified: bool
    customer_id: Optional[uuid.UUID] = None
    courier_id: Optional[uuid.UUID] = None
    merchant_id: Optional[uuid.UUID] = None
