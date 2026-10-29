import uuid

from fastapi import HTTPException, status

from models import Merchant
from repositories.merchant_repo import MerchantRepository


class MerchantService:
    def __init__(self, merchant_repo: MerchantRepository):
        self.merchant_repo = merchant_repo

    def verify(self, merchant_id: uuid.UUID) -> Merchant:
        merchant = self.merchant_repo.get_by_id(merchant_id)
        if merchant is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Merchant not found")
        merchant.is_verified = True
        return self.merchant_repo.save(merchant)
