import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from core.dependencies import get_current_merchant_id, get_restaurant_service
from schemas.restaurant_schema import (
    RestaurantCreate,
    RestaurantDetailResponse,
    RestaurantResponse,
    RestaurantUpdate,
)
from services.restaurant_service import RestaurantService

router = APIRouter(prefix="/restaurants", tags=["restaurants"])


@router.post("", response_model=RestaurantResponse, status_code=status.HTTP_201_CREATED)
def create_restaurant(
    data: RestaurantCreate,
    merchant_id: Annotated[uuid.UUID, Depends(get_current_merchant_id)],
    restaurant_service: Annotated[RestaurantService, Depends(get_restaurant_service)],
):
    return restaurant_service.create(merchant_id, data)


@router.get("", response_model=list[RestaurantResponse])
def list_restaurants(
    merchant_id: Annotated[uuid.UUID, Depends(get_current_merchant_id)],
    restaurant_service: Annotated[RestaurantService, Depends(get_restaurant_service)],
):
    return restaurant_service.get_all(merchant_id)


@router.get("/{restaurant_id}", response_model=RestaurantDetailResponse)
def get_restaurant(
    restaurant_id: uuid.UUID,
    merchant_id: Annotated[uuid.UUID, Depends(get_current_merchant_id)],
    restaurant_service: Annotated[RestaurantService, Depends(get_restaurant_service)],
):
    return restaurant_service.get_with_menu(merchant_id, restaurant_id)


@router.patch("/{restaurant_id}", response_model=RestaurantResponse)
def update_restaurant(
    restaurant_id: uuid.UUID,
    data: RestaurantUpdate,
    merchant_id: Annotated[uuid.UUID, Depends(get_current_merchant_id)],
    restaurant_service: Annotated[RestaurantService, Depends(get_restaurant_service)],
):
    return restaurant_service.update(merchant_id, restaurant_id, data)


@router.delete("/{restaurant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_restaurant(
    restaurant_id: uuid.UUID,
    merchant_id: Annotated[uuid.UUID, Depends(get_current_merchant_id)],
    restaurant_service: Annotated[RestaurantService, Depends(get_restaurant_service)],
):
    restaurant_service.delete(merchant_id, restaurant_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
