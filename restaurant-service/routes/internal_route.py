from typing import Annotated

from fastapi import APIRouter, Depends

from core.dependencies import get_item_service
from schemas.item_schema import OrderableItemResponse
from services.item_service import ItemService

# Mounted outside /api, so the gateway never forwards these; for service-to-service calls only.
router = APIRouter(prefix="/internal", tags=["internal"])


@router.get("/items/{item_id}", response_model=OrderableItemResponse)
def get_orderable_item(
    item_id: int,
    item_service: Annotated[ItemService, Depends(get_item_service)],
):
    return item_service.get_orderable(item_id)
