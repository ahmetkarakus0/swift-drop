import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from models.courier import Courier
    from models.customer import Customer
    from models.merchant import Merchant


class Address(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "addresses"
    __table_args__ = (
        CheckConstraint(
            "num_nonnulls(customer_id, courier_id, merchant_id) = 1",
            name="ck_addresses_single_owner",
        ),
    )

    customer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), index=True
    )
    courier_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("couriers.id", ondelete="CASCADE"), index=True
    )
    merchant_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("merchants.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    district: Mapped[str] = mapped_column(String(100), nullable=False)
    neighborhood: Mapped[str] = mapped_column(String(100), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(20), nullable=False)
    address_line1: Mapped[str] = mapped_column(String(255), nullable=False)
    address_line2: Mapped[Optional[str]] = mapped_column(String(255))
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)

    customer: Mapped[Optional["Customer"]] = relationship(back_populates="addresses")
    courier: Mapped[Optional["Courier"]] = relationship(back_populates="addresses")
    merchant: Mapped[Optional["Merchant"]] = relationship(back_populates="addresses")
