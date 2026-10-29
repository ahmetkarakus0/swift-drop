from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from core.dependencies import get_health_service
from schemas.health_schema import HealthResponse
from services.health_service import HealthService

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    response_model_exclude_none=True,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": HealthResponse}},
)
def health(
    response: Response,
    health_service: Annotated[HealthService, Depends(get_health_service)],
):
    result = health_service.check()
    if result.status == "down":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return result
