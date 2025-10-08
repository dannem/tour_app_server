from sqlalchemy.orm import Session, joinedload

import models
import schemas


def get_tour(db: Session, tour_id: int):
    # Eagerly load waypoints when fetching a single tour
    return (
        db.query(models.Tour)
        .options(joinedload(models.Tour.waypoints))
        .filter(models.Tour.id == tour_id)
        .first()
    )


def get_tours(db: Session, skip: int = 0, limit: int = 100):
    # Eagerly load waypoints for all tours in the list
    return (
        db.query(models.Tour)
        .options(joinedload(models.Tour.waypoints))
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_tour(db: Session, tour: schemas.TourCreate):
    db_tour = models.Tour(name=tour.name, description=tour.description)
    db.add(db_tour)
    db.commit()
    db.refresh(db_tour)
    return db_tour


def create_tour_waypoint(
    db: Session, waypoint: schemas.WaypointCreate, tour_id: int, audio_filename: str
):
    # Create waypoint with all fields including name
    waypoint_dict = waypoint.model_dump(
        exclude={"address"}
    )  # Exclude address as it's not in the model
    db_waypoint = models.Waypoint(
        **waypoint_dict, tour_id=tour_id, audio_filename=audio_filename
    )
    db.add(db_waypoint)
    db.commit()
    db.refresh(db_waypoint)
    return db_waypoint
