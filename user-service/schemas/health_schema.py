from typing import Literal, Optional

from pydantic import BaseModel

HealthStatus = Literal["up", "down"]


class ServiceHealth(BaseModel):
    status: HealthStatus
    latency_ms: Optional[float] = None


class HealthResponse(BaseModel):
    status: HealthStatus
    services: dict[str, ServiceHealth]
