import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from schemas.common import LongText, PhoneNumber, PostalCode, ShortText


class AddressCreate(BaseModel):
    title: ShortText
    phone_number: PhoneNumber
    country: ShortText
    city: ShortText
    district: ShortText
    neighborhood: ShortText
    postal_code: PostalCode
    address_line1: LongText
    address_line2: Optional[LongText] = None


class AddressResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    phone_number: str
    country: str
    city: str
    district: str
    neighborhood: str
    postal_code: str
    address_line1: str
    address_line2: Optional[str]
    is_default: bool
    created_at: datetime
