from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, CreatedAtMixin, IntegerPrimaryKeyMixin

if TYPE_CHECKING:
    from models.category import Category


class Item(IntegerPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "items"
    __table_args__ = (
        CheckConstraint("price >= 0", name="ck_items_price_non_negative"),
    )

    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)

    category: Mapped["Category"] = relationship(back_populates="items")
