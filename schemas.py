# File: tour_app_server/schemas.py

from typing import List, Optional

from pydantic import BaseModel, root_validator


# --- Waypoint Schemas ---
class WaypointBase(BaseModel):
    name: Optional[str] = None  # Added name field
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class WaypointCreate(WaypointBase):
    address: Optional[str] = None

    @root_validator(pre=True)
    def check_at_least_one_location_field(cls, values):
        if not (
            values.get("latitude") is not None and values.get("longitude") is not None
        ) and not values.get("address"):
            raise ValueError(
                "Either 'latitude' and 'longitude' or 'address' must be provided"
            )
        return values


class Waypoint(WaypointBase):
    id: int
    tour_id: int
    audio_filename: Optional[str] = None

    class Config:
        from_attributes = True


# --- Tour Schemas ---
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
