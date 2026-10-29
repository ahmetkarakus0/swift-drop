from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict

from schemas.common import Description, LongText, PatchModel, Price


class ItemCreate(BaseModel):
    name: LongText
    description: Optional[Description] = None
    price: Price
    is_active: bool = True


class ItemUpdate(PatchModel):
    nullable_fields = frozenset({"description"})

    name: Optional[LongText] = None
    description: Optional[Description] = None
    price: Optional[Price] = None
    is_active: Optional[bool] = None


class ItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int
    name: str
    description: Optional[str]
    price: Decimal
    is_active: bool
    created_at: datetime
