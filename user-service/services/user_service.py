from typing import Optional

from models import User, UserRole
from repositories.user_repo import UserRepository


class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def get_all(self, role: Optional[UserRole], limit: int, offset: int) -> list[User]:
        return self.user_repo.get_all(role, limit, offset)
