# File: tour_app_server/main.py

import os
from typing import List, Optional

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles
from geopy.exc import GeocoderTimedOut
from geopy.geocoders import Nominatim
from sqlalchemy.orm import Session

import crud
import models
import schemas
from database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.get("/")
def read_root():
    return {"message": "Welcome to the Tour App API"}


# Create uploads directory if it doesn't exist
if not os.path.exists("uploads"):
    os.makedirs("uploads")


# Dependency to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/tours", response_model=schemas.Tour, status_code=201)
def create_tour(tour: schemas.TourCreate, db: Session = Depends(get_db)):
    return crud.create_tour(db=db, tour=tour)


@app.get("/tours", response_model=List[schemas.Tour])
def read_tours(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    tours = crud.get_tours(db, skip=skip, limit=limit)
    return tours


@app.get("/tours/{tour_id}", response_model=schemas.Tour)
def read_tour(tour_id: int, db: Session = Depends(get_db)):
    db_tour = crud.get_tour(db, tour_id=tour_id)
    if db_tour is None:
        raise HTTPException(status_code=404, detail="Tour not found")
    return db_tour


@app.post("/tours/{tour_id}/waypoints", response_model=schemas.Waypoint)
async def create_waypoint_for_tour(
    tour_id: int,
    latitude: float = Form(...),
    longitude: float = Form(...),
    audio_file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # Check if the tour exists
    db_tour = crud.get_tour(db, tour_id=tour_id)
    if not db_tour:
        raise HTTPException(status_code=404, detail="Tour not found")

    # Save the uploaded audio file
    file_location = f"uploads/{audio_file.filename}"
    with open(file_location, "wb+") as file_object:
        file_object.write(await audio_file.read())

    # Create the waypoint schema and save it to the database
    waypoint_data = schemas.WaypointCreate(latitude=latitude, longitude=longitude)
    return crud.create_tour_waypoint(
        db=db,
        waypoint=waypoint_data,
        tour_id=tour_id,
        audio_filename=audio_file.filename,
    )


@app.post("/tours/{tour_id}/waypoints-from-home", response_model=schemas.Waypoint)
async def create_home_waypoint(
    tour_id: int,
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    address: Optional[str] = Form(None),
    audio_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    # Check if the tour exists
    db_tour = crud.get_tour(db, tour_id=tour_id)
    if not db_tour:
        raise HTTPException(status_code=404, detail="Tour not found")

    # Handle geocoding if an address is provided
    if address:
        geolocator = Nominatim(user_agent="tour_app")
        try:
            location = geolocator.geocode(address)
            if not location:
                raise HTTPException(status_code=400, detail="Address not found")
            latitude = location.latitude
            longitude = location.longitude
        except GeocoderTimedOut:
            raise HTTPException(status_code=500, detail="Geocoding service timed out")
    elif latitude is None or longitude is None:
        raise HTTPException(
            status_code=400,
            detail="Either address or latitude/longitude must be provided",
        )

    # Save the optional audio file
    audio_filename = None
    if audio_file:
        file_location = f"uploads/{audio_file.filename}"
        with open(file_location, "wb+") as file_object:
            file_object.write(await audio_file.read())
        audio_filename = audio_file.filename

    # Create the waypoint schema and save it to the database
    waypoint_data = schemas.WaypointCreate(latitude=latitude, longitude=longitude)
    return crud.create_tour_waypoint(
        db=db,
        waypoint=waypoint_data,
        tour_id=tour_id,
        audio_filename=audio_filename,
    )
