from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator

from core.security import BCRYPT_MAX_BYTES
from models import VehicleType
from schemas.address_schema import AddressCreate
from schemas.common import Email, Name, NormalizedEmail, PhoneNumber
from schemas.courier_schema import CourierResponse
from schemas.customer_schema import CustomerResponse
from schemas.user_schema import UserResponse

VehiclePlate = Annotated[
    str, StringConstraints(strip_whitespace=True, to_upper=True, min_length=1, max_length=20)
]

_EXAMPLE_ADDRESS = {
    "title": "Home",
    "phone_number": "+10000000000",
    "country": "Example Country",
    "city": "Example City",
    "district": "Example District",
    "neighborhood": "Example Neighborhood",
    "postal_code": "00000",
    "address_line1": "Example Street No: 1",
    "address_line2": None,
}


class BaseRegisterRequest(BaseModel):
    email: Email
    password: str = Field(min_length=8)
    first_name: Name
    last_name: Name
    phone_number: PhoneNumber
    address: AddressCreate

    @field_validator("password")
    @classmethod
    def password_fits_bcrypt(cls, value: str) -> str:
        if len(value.encode("utf-8")) > BCRYPT_MAX_BYTES:
            raise ValueError(f"Password must be at most {BCRYPT_MAX_BYTES} bytes")
        return value


class CustomerRegisterRequest(BaseRegisterRequest):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "email": "john.doe@example.com",
                    "password": "Password123!",
                    "first_name": "John",
                    "last_name": "Doe",
                    "phone_number": "+10000000000",
                    "address": _EXAMPLE_ADDRESS,
                }
            ]
        }
    )


class CourierRegisterRequest(BaseRegisterRequest):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "email": "jane.doe@example.com",
                    "password": "Password123!",
                    "first_name": "Jane",
                    "last_name": "Doe",
                    "phone_number": "+10000000000",
                    "vehicle_type": "motorcycle",
                    "vehicle_plate": "AA 000 AA",
                    "address": _EXAMPLE_ADDRESS,
                }
            ]
        }
    )

    vehicle_type: VehicleType
    vehicle_plate: Optional[VehiclePlate] = None

    @model_validator(mode="after")
    def plate_matches_vehicle(self) -> "CourierRegisterRequest":
        if self.vehicle_type == VehicleType.BICYCLE:
            if self.vehicle_plate is not None:
                raise ValueError("Bicycles must not have a vehicle plate")
        elif self.vehicle_plate is None:
            raise ValueError(f"vehicle_plate is required for {self.vehicle_type.value}")
        return self


class CustomerRegisterResponse(UserResponse):
    customer: CustomerResponse


class CourierRegisterResponse(UserResponse):
    courier: CourierResponse


class LoginRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"examples": [{"email": "john.doe@example.com", "password": "Password123!"}]}
    )

    email: NormalizedEmail
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
