import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, CreatedAtMixin, IntegerPrimaryKeyMixin

if TYPE_CHECKING:
    from models.item import Item
    from models.restaurant import Restaurant


class Category(IntegerPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "categories"

    restaurant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("restaurants.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)

    restaurant: Mapped["Restaurant"] = relationship(back_populates="categories")
    items: Mapped[list["Item"]] = relationship(
        back_populates="category", cascade="all, delete-orphan", order_by="Item.id"
    )
