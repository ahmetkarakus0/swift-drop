import uuid

from fastapi import HTTPException, status

from models import Merchant, MerchantStatus
from repositories.merchant_repo import MerchantRepository


class MerchantService:
    def __init__(self, merchant_repo: MerchantRepository):
        self.merchant_repo = merchant_repo

    def verify(self, merchant_id: uuid.UUID) -> Merchant:
        merchant = self._get(merchant_id)
        merchant.is_verified = True
        return self.merchant_repo.save(merchant)

    def set_status(self, merchant_id: uuid.UUID, new_status: MerchantStatus) -> Merchant:
        merchant = self._get(merchant_id)
        merchant.status = new_status
        return self.merchant_repo.save(merchant)

    def _get(self, merchant_id: uuid.UUID) -> Merchant:
        merchant = self.merchant_repo.get_by_id(merchant_id)
        if merchant is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Merchant not found")
        return merchant
