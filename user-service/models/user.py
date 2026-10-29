import enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from models.courier import Courier
    from models.customer import Customer
    from models.merchant import Merchant


class UserRole(str, enum.Enum):
    CUSTOMER = "customer"
    COURIER = "courier"
    MERCHANT = "merchant"
    ADMIN = "admin"


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)

    customer: Mapped[Optional["Customer"]] = relationship(back_populates="user", uselist=False)
    courier: Mapped[Optional["Courier"]] = relationship(back_populates="user", uselist=False)
    merchant: Mapped[Optional["Merchant"]] = relationship(back_populates="user", uselist=False)
