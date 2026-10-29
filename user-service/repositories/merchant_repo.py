import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from models import Merchant


class MerchantRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, merchant_id: uuid.UUID) -> Optional[Merchant]:
        return self.db.scalar(
            select(Merchant)
            .where(Merchant.id == merchant_id)
            .options(selectinload(Merchant.addresses))
        )

    def save(self, merchant: Merchant) -> Merchant:
        self.db.commit()
        return merchant
