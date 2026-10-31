import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from models import User, UserRole


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.scalar(select(User).where(User.email == email))

    def get_all(self, role: Optional[UserRole], limit: int, offset: int) -> list[User]:
        query = select(User).order_by(User.created_at.desc(), User.id)
        if role is not None:
            query = query.where(User.role == role)
        return list(self.db.scalars(query.limit(limit).offset(offset)))

    def get_by_verification_link(self, token: str) -> Optional[User]:
        return self.db.scalar(select(User).where(User.user_verification_link == token))

    def create(self, user: User) -> User:
        """Saves the user together with its related profile and addresses in one transaction."""
        self.db.add(user)
        self.db.commit()
        return user

    def save(self, user: User) -> User:
        self.db.commit()
        return user
