import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from schemas.common import LongText, PatchModel, PhoneNumber, PostalCode, ShortText


class RestaurantCreate(BaseModel):
    name: LongText
    phone_number: PhoneNumber
    country: ShortText
    city: ShortText
    district: ShortText
    neighborhood: ShortText
    postal_code: PostalCode
    address_line1: LongText
    address_line2: Optional[LongText] = None
    is_open: bool = False


class RestaurantUpdate(PatchModel):
    nullable_fields = frozenset({"address_line2"})

    name: Optional[LongText] = None
    phone_number: Optional[PhoneNumber] = None
    country: Optional[ShortText] = None
    city: Optional[ShortText] = None
    district: Optional[ShortText] = None
    neighborhood: Optional[ShortText] = None
    postal_code: Optional[PostalCode] = None
    address_line1: Optional[LongText] = None
    address_line2: Optional[LongText] = None
    is_open: Optional[bool] = None


class RestaurantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    merchant_id: uuid.UUID
    name: str
    phone_number: str
    is_open: bool
    rating: float
    is_active: bool
    country: str
    city: str
    district: str
    neighborhood: str
    postal_code: str
    address_line1: str
    address_line2: Optional[str]
    created_at: datetime
