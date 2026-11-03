import uuid
from typing import Optional

from pydantic import BaseModel


class Coordinates(BaseModel):
    latitude: float
    longitude: float


class CourierCandidate(BaseModel):
    courier_id: uuid.UUID
    distance_km: float


class CourierSearchResult(BaseModel):
    # The radius the candidates were found in; None when no courier was found.
    radius_km: Optional[float] = None
    candidates: list[CourierCandidate] = []
