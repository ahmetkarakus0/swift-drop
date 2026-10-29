import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from core.dependencies import get_merchant_service, require_roles
from models import UserRole
from schemas.merchant_schema import MerchantResponse
from services.merchant_service import MerchantService

router = APIRouter(prefix="/merchants", tags=["merchants"])


@router.post(
    "/{merchant_id}/verify",
    response_model=MerchantResponse,
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
def verify_merchant(
    merchant_id: uuid.UUID,
    merchant_service: Annotated[MerchantService, Depends(get_merchant_service)],
):
    return merchant_service.verify(merchant_id)
