import enum
import uuid
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, Enum, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from models.order_item import OrderItem


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY_FOR_PICKUP = "ready_for_pickup"
    ON_THE_WAY = "on_the_way"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class Order(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint("total_price >= 0", name="ck_orders_total_price_non_negative"),
    )

    # References users.id in user_db; cross-database, so no foreign key.
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True, nullable=False)
    # References restaurants.id in restaurant_db; cross-database, so no foreign key.
    restaurant_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True, nullable=False)
    # References couriers.id in user_db; cross-database, so no foreign key.
    courier_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, index=True)
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="order_status", values_callable=lambda e: [m.value for m in e]),
        default=OrderStatus.PENDING,
        server_default=OrderStatus.PENDING.value,
        index=True,
        nullable=False,
    )
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    delivery_address: Mapped[str] = mapped_column(String(500), nullable=False)

    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan", order_by="OrderItem.item_name"
    )
