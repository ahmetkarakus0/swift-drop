import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from core.dependencies import get_current_merchant_id, get_item_service
from schemas.item_schema import ItemCreate, ItemResponse, ItemUpdate
from services.item_service import ItemService

router = APIRouter(tags=["items"])


@router.post(
    "/categories/{category_id}/items",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_item(
    category_id: int,
    data: ItemCreate,
    merchant_id: Annotated[uuid.UUID, Depends(get_current_merchant_id)],
    item_service: Annotated[ItemService, Depends(get_item_service)],
):
    return item_service.create(merchant_id, category_id, data)


@router.get("/categories/{category_id}/items", response_model=list[ItemResponse])
def list_items(
    category_id: int,
    merchant_id: Annotated[uuid.UUID, Depends(get_current_merchant_id)],
    item_service: Annotated[ItemService, Depends(get_item_service)],
):
    return item_service.get_all(merchant_id, category_id)


@router.get("/items/{item_id}", response_model=ItemResponse)
def get_item(
    item_id: int,
    merchant_id: Annotated[uuid.UUID, Depends(get_current_merchant_id)],
    item_service: Annotated[ItemService, Depends(get_item_service)],
):
    return item_service.get(merchant_id, item_id)


@router.patch("/items/{item_id}", response_model=ItemResponse)
def update_item(
    item_id: int,
    data: ItemUpdate,
    merchant_id: Annotated[uuid.UUID, Depends(get_current_merchant_id)],
    item_service: Annotated[ItemService, Depends(get_item_service)],
):
    return item_service.update(merchant_id, item_id, data)


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    item_id: int,
    merchant_id: Annotated[uuid.UUID, Depends(get_current_merchant_id)],
    item_service: Annotated[ItemService, Depends(get_item_service)],
):
    item_service.delete(merchant_id, item_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
