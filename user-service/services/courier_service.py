import uuid

from fastapi import HTTPException, status

from models import Courier
from repositories.courier_repo import CourierRepository


class CourierService:
    def __init__(self, courier_repo: CourierRepository):
        self.courier_repo = courier_repo

    def verify(self, courier_id: uuid.UUID) -> Courier:
        courier = self._get(courier_id)
        courier.is_verified = True
        return self.courier_repo.save(courier)

    def _get(self, courier_id: uuid.UUID) -> Courier:
        courier = self.courier_repo.get_by_id(courier_id)
        if courier is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Courier not found")
        return courier
