from pydantic import BaseModel, Field

# Redis GEO indexes only accept latitudes within the Web Mercator range.
MAX_LATITUDE = 85.05112878


class CourierLocationUpdate(BaseModel):
    latitude: float = Field(ge=-MAX_LATITUDE, le=MAX_LATITUDE)
    longitude: float = Field(ge=-180, le=180)


class Coordinates(BaseModel):
    latitude: float
    longitude: float
