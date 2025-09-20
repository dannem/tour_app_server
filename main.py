# File: tour_app_server/main.py

import os
from typing import List

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles
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


# UPDATED WAYPOINT ENDPOINT
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
