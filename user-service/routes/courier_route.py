import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from core.dependencies import get_courier_service, require_roles
from models import UserRole
from schemas.courier_schema import CourierResponse
from services.courier_service import CourierService

router = APIRouter(prefix="/couriers", tags=["couriers"])


@router.post(
    "/{courier_id}/verify",
    response_model=CourierResponse,
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
def verify_courier(
    courier_id: uuid.UUID,
    courier_service: Annotated[CourierService, Depends(get_courier_service)],
):
    return courier_service.verify(courier_id)
