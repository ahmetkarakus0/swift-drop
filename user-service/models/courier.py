import enum
import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from models.address import Address
    from models.user import User


class VehicleType(str, enum.Enum):
    BICYCLE = "bicycle"
    MOTORCYCLE = "motorcycle"
    CAR = "car"


class Courier(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "couriers"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    vehicle_type: Mapped[VehicleType] = mapped_column(
        Enum(VehicleType, name="vehicle_type", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )
    # Bicycles have no plate.
    vehicle_plate: Mapped[Optional[str]] = mapped_column(String(20))
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)

    user: Mapped["User"] = relationship(back_populates="courier")
    addresses: Mapped[list["Address"]] = relationship(
        back_populates="courier", cascade="all, delete-orphan"
    )
