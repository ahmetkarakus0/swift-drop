import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from schemas.common import PatchModel, ShortText


class CategoryCreate(BaseModel):
    name: ShortText
    is_active: bool = True


class CategoryUpdate(PatchModel):
    name: Optional[ShortText] = None
    is_active: Optional[bool] = None


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    restaurant_id: uuid.UUID
    name: str
    is_active: bool
    created_at: datetime
