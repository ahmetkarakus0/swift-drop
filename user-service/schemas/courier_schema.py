import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from models import VehicleType
from schemas.address_schema import AddressResponse


class CourierResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    first_name: str
    last_name: str
    phone_number: str
    vehicle_type: VehicleType
    vehicle_plate: Optional[str]
    is_approved: bool
    created_at: datetime
    addresses: list[AddressResponse]
