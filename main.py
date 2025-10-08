import os
from typing import List, Optional

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from geopy.geocoders import Nominatim
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

import crud
import models
import schemas
from database import SessionLocal, engine


# Automatic migration - add name column if it doesn't exist
def migrate_database():
    try:
        inspector = inspect(engine)
        columns = [col["name"] for col in inspector.get_columns("waypoints")]

        if "name" not in columns:
            print("🔄 Adding 'name' column to waypoints table...")
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE waypoints ADD COLUMN name TEXT"))
                conn.commit()
            print("✅ Migration completed!")
        else:
            print("✅ Database schema is up to date")
    except Exception as e:
        print(f"⚠️  Migration error (this is OK if tables don't exist yet): {e}")


# Run migration before creating tables
migrate_database()
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory if it doesn't exist
if not os.path.exists("uploads"):
    os.makedirs("uploads")

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

geolocator = Nominatim(user_agent="tour_app")


@app.get("/")
def read_root():
    return {"message": "Welcome to the Tour App API", "status": "running"}


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
    name: str = Form("Unnamed Waypoint"),  # Default value if not provided
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
    waypoint_data = schemas.WaypointCreate(
        name=name, latitude=latitude, longitude=longitude
    )
    return crud.create_tour_waypoint(
        db=db,
        waypoint=waypoint_data,
        tour_id=tour_id,
        audio_filename=audio_file.filename,
    )


@app.post("/tours/{tour_id}/waypoints/from_home", response_model=schemas.Waypoint)
async def create_waypoint_from_home(
    tour_id: int,
    audio_file: UploadFile = File(...),
    name: Optional[str] = Form("Home"),
    address: Optional[str] = Form(None),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    db: Session = Depends(get_db),
):
    db_tour = crud.get_tour(db, tour_id=tour_id)
    if not db_tour:
        raise HTTPException(status_code=404, detail="Tour not found")

    if address:
        try:
            location = geolocator.geocode(address)
            if not location:
                raise HTTPException(
                    status_code=400, detail="Address could not be geocoded"
                )
            latitude = location.latitude
            longitude = location.longitude
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Geocoding service error: {e}")
    elif latitude is None or longitude is None:
        raise HTTPException(
            status_code=400,
            detail="Either an address or latitude/longitude must be provided.",
        )

    file_location = f"uploads/{audio_file.filename}"
    with open(file_location, "wb+") as file_object:
        file_object.write(await audio_file.read())

    waypoint_data = schemas.WaypointCreate(
        name=name, latitude=latitude, longitude=longitude
    )
    return crud.create_tour_waypoint(
        db=db,
        waypoint=waypoint_data,
        tour_id=tour_id,
        audio_filename=audio_file.filename,
    )
