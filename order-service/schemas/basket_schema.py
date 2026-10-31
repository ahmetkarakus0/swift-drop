import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, computed_field

from schemas.common import Quantity


class BasketItemCreate(BaseModel):
    item_id: int
    quantity: Quantity = 1


class BasketItemUpdate(BaseModel):
    quantity: Quantity


class BasketItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    item_id: int
    item_name: str
    quantity: int
    price: Decimal


class BasketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    restaurant_id: uuid.UUID
    items: list[BasketItemResponse]
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def total_price(self) -> Decimal:
        return sum((item.price * item.quantity for item in self.items), Decimal("0"))
