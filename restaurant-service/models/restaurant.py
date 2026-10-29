import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, CheckConstraint, Float, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from models.category import Category


class Restaurant(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "restaurants"
    __table_args__ = (
        CheckConstraint("rating >= 0 AND rating <= 5", name="ck_restaurants_rating_range"),
    )

    # References merchants.id in users_db; cross-database, so no foreign key.
    merchant_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    is_open: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    rating: Mapped[float] = mapped_column(Float, default=0, server_default="0", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    district: Mapped[str] = mapped_column(String(100), nullable=False)
    neighborhood: Mapped[str] = mapped_column(String(100), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(20), nullable=False)
    address_line1: Mapped[str] = mapped_column(String(255), nullable=False)
    address_line2: Mapped[Optional[str]] = mapped_column(String(255))

    categories: Mapped[list["Category"]] = relationship(
        back_populates="restaurant", cascade="all, delete-orphan", order_by="Category.id"
    )
