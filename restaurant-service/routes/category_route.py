import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from core.dependencies import get_category_service, get_current_merchant_id
from schemas.category_schema import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
    CategoryWithItemsResponse,
)
from services.category_service import CategoryService

router = APIRouter(tags=["categories"])


@router.post(
    "/restaurants/{restaurant_id}/categories",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_category(
    restaurant_id: uuid.UUID,
    data: CategoryCreate,
    merchant_id: Annotated[uuid.UUID, Depends(get_current_merchant_id)],
    category_service: Annotated[CategoryService, Depends(get_category_service)],
):
    return category_service.create(merchant_id, restaurant_id, data)


@router.get("/restaurants/{restaurant_id}/categories", response_model=list[CategoryResponse])
def list_categories(
    restaurant_id: uuid.UUID,
    merchant_id: Annotated[uuid.UUID, Depends(get_current_merchant_id)],
    category_service: Annotated[CategoryService, Depends(get_category_service)],
):
    return category_service.get_all(merchant_id, restaurant_id)


@router.get("/categories/{category_id}", response_model=CategoryWithItemsResponse)
def get_category(
    category_id: int,
    merchant_id: Annotated[uuid.UUID, Depends(get_current_merchant_id)],
    category_service: Annotated[CategoryService, Depends(get_category_service)],
):
    return category_service.get_with_items(merchant_id, category_id)


@router.patch("/categories/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    data: CategoryUpdate,
    merchant_id: Annotated[uuid.UUID, Depends(get_current_merchant_id)],
    category_service: Annotated[CategoryService, Depends(get_category_service)],
):
    return category_service.update(merchant_id, category_id, data)


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    merchant_id: Annotated[uuid.UUID, Depends(get_current_merchant_id)],
    category_service: Annotated[CategoryService, Depends(get_category_service)],
):
    category_service.delete(merchant_id, category_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
