import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from core.dependencies import get_current_courier_id, get_location_service
from schemas.location_schema import CourierLocationUpdate
from services.location_service import LocationService

router = APIRouter(prefix="/couriers", tags=["couriers"])


@router.put("/location", status_code=status.HTTP_204_NO_CONTENT)
def update_location(
    data: CourierLocationUpdate,
    courier_id: Annotated[uuid.UUID, Depends(get_current_courier_id)],
    location_service: Annotated[LocationService, Depends(get_location_service)],
):
    location_service.update_location(courier_id, data)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
