import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from models import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.scalar(select(User).where(User.email == email))

    def create(self, user: User) -> User:
        """Saves the user together with its related profile and addresses in one transaction."""
        self.db.add(user)
        self.db.commit()
        return user
