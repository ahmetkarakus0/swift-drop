import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from schemas.address_schema import AddressResponse


class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    first_name: str
    last_name: str
    phone_number: str
    created_at: datetime
    addresses: list[AddressResponse]
