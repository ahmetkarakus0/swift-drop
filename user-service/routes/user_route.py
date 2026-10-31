from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query

from core.dependencies import get_user_service, require_roles
from models import UserRole
from schemas.user_schema import UserResponse
from services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "",
    response_model=list[UserResponse],
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
def list_users(
    user_service: Annotated[UserService, Depends(get_user_service)],
    role: Optional[UserRole] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    return user_service.get_all(role, limit, offset)
