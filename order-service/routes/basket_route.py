import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from core.dependencies import get_basket_service, get_current_customer_user_id
from schemas.basket_schema import BasketItemCreate, BasketItemUpdate, BasketResponse
from services.basket_service import BasketService

router = APIRouter(prefix="/baskets", tags=["baskets"])


@router.post("/items", response_model=BasketResponse, status_code=status.HTTP_201_CREATED)
def add_basket_item(
    data: BasketItemCreate,
    user_id: Annotated[uuid.UUID, Depends(get_current_customer_user_id)],
    basket_service: Annotated[BasketService, Depends(get_basket_service)],
):
    return basket_service.add_item(user_id, data)


@router.get("", response_model=list[BasketResponse])
def list_baskets(
    user_id: Annotated[uuid.UUID, Depends(get_current_customer_user_id)],
    basket_service: Annotated[BasketService, Depends(get_basket_service)],
):
    return basket_service.get_all(user_id)


@router.get("/{basket_id}", response_model=BasketResponse)
def get_basket(
    basket_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_customer_user_id)],
    basket_service: Annotated[BasketService, Depends(get_basket_service)],
):
    return basket_service.get(user_id, basket_id)


@router.patch("/{basket_id}/items/{basket_item_id}", response_model=BasketResponse)
def update_basket_item(
    basket_id: uuid.UUID,
    basket_item_id: uuid.UUID,
    data: BasketItemUpdate,
    user_id: Annotated[uuid.UUID, Depends(get_current_customer_user_id)],
    basket_service: Annotated[BasketService, Depends(get_basket_service)],
):
    return basket_service.update_item(user_id, basket_id, basket_item_id, data)


@router.delete("/{basket_id}/items/{basket_item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_basket_item(
    basket_id: uuid.UUID,
    basket_item_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_customer_user_id)],
    basket_service: Annotated[BasketService, Depends(get_basket_service)],
):
    basket_service.remove_item(user_id, basket_id, basket_item_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/{basket_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_basket(
    basket_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_customer_user_id)],
    basket_service: Annotated[BasketService, Depends(get_basket_service)],
):
    basket_service.delete(user_id, basket_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
