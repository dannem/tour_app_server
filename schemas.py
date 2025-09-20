# File: tour_app_server/schemas.py

from typing import List, Optional

from pydantic import BaseModel


# --- Waypoint Schemas ---
class WaypointBase(BaseModel):
    latitude: float
    longitude: float


# ADD THIS NEW CLASS
class WaypointCreate(WaypointBase):
    pass


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
