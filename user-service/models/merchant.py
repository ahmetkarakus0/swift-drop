import enum
import uuid
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, CheckConstraint, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from models.address import Address
    from models.user import User


class MerchantStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Merchant(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "merchants"
    __table_args__ = (
        CheckConstraint(
            "commission_rate >= 0 AND commission_rate <= 100",
            name="ck_merchants_commission_rate_range",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    business_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    tax_number: Mapped[str] = mapped_column(String(20), nullable=False)
    tax_office: Mapped[str] = mapped_column(String(100), nullable=False)
    iban: Mapped[str] = mapped_column(String(34), nullable=False)
    status: Mapped[MerchantStatus] = mapped_column(
        Enum(MerchantStatus, name="merchant_status", values_callable=lambda e: [m.value for m in e]),
        default=MerchantStatus.PENDING,
        server_default=MerchantStatus.PENDING.value,
        nullable=False,
    )
    # Percentage (e.g. 12.50). Set by an admin; NULL until then.
    commission_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    # Admin-only.
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)

    user: Mapped["User"] = relationship(back_populates="merchant")
    addresses: Mapped[list["Address"]] = relationship(
        back_populates="merchant", cascade="all, delete-orphan"
    )
