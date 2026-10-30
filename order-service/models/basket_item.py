import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Integer, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from models.basket import Basket


class BasketItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "basket_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_basket_items_quantity_positive"),
        CheckConstraint("price >= 0", name="ck_basket_items_price_non_negative"),
    )

    basket_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("baskets.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # References items.id in restaurant_db; cross-database, so no foreign key.
    item_id: Mapped[int] = mapped_column(Integer, nullable=False)
    item_name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    basket: Mapped["Basket"] = relationship(back_populates="items")
