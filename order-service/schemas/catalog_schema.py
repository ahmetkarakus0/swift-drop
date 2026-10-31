import uuid
from decimal import Decimal

from pydantic import BaseModel


class CatalogItem(BaseModel):
    """restaurant-service's GET /internal/items/{item_id} response."""

    id: int
    name: str
    price: Decimal
    restaurant_id: uuid.UUID
    restaurant_is_open: bool
