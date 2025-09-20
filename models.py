# File: tour_app_server/models.py

from sqlalchemy import Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from database import Base


class Tour(Base):
    __tablename__ = "tours"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)

    waypoints = relationship("Waypoint", back_populates="tour")


class Waypoint(Base):
    __tablename__ = "waypoints"

    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    audio_filename = Column(String, nullable=True)
    tour_id = Column(Integer, ForeignKey("tours.id"))

    tour = relationship("Tour", back_populates="waypoints")
