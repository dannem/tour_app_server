from typing import List, Optional

from pydantic import BaseModel, field_validator


class WaypointBase(BaseModel):
    name: Optional[str] = "Unnamed Waypoint"
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class WaypointCreate(WaypointBase):
    address: Optional[str] = None

    @field_validator("latitude", "longitude", "address")
    @classmethod
    def check_location_fields(cls, v, info):
        # This validator will be called for all three fields
        return v


class Waypoint(WaypointBase):
    id: int
    tour_id: int
    audio_filename: Optional[str] = None

    class Config:
        from_attributes = True


class TourBase(BaseModel):
    name: str
    description: str


class TourCreate(TourBase):
    pass


class Tour(TourBase):
    id: int
    waypoints: List[Waypoint] = []

    class Config:
        from_attributes = True
