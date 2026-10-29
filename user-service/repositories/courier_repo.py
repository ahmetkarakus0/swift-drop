import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from models import Courier


class CourierRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, courier_id: uuid.UUID) -> Optional[Courier]:
        return self.db.scalar(
            select(Courier)
            .where(Courier.id == courier_id)
            .options(selectinload(Courier.addresses))
        )

    def save(self, courier: Courier) -> Courier:
        self.db.commit()
        return courier
