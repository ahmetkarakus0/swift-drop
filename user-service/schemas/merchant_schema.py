import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict

from models import MerchantStatus
from schemas.address_schema import AddressResponse


class MerchantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    business_name: str
    phone_number: str
    tax_number: str
    tax_office: str
    iban: str
    status: MerchantStatus
    commission_rate: Optional[Decimal]
    created_at: datetime
    updated_at: datetime
    addresses: list[AddressResponse]
