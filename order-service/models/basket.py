import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from models.basket_item import BasketItem


class Basket(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "baskets"

    # References users.id in user_db; cross-database, so no foreign key.
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True, nullable=False)
    # References restaurants.id in restaurant_db; cross-database, so no foreign key.
    restaurant_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True, nullable=False)

    items: Mapped[list["BasketItem"]] = relationship(
        back_populates="basket", cascade="all, delete-orphan", order_by="BasketItem.created_at"
    )
