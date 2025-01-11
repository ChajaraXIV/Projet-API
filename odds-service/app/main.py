import asyncio
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import Column, Integer, String, Float, create_engine, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, ConfigDict
from dotenv import load_dotenv
from typing import Optional
from datetime import datetime, timedelta
import os

# Initialize FastAPI app
app = FastAPI()

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in the environment variables")

# Initialize database engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create the Base for SQLAlchemy models
Base = declarative_base()

# Valid ENUM values for phase and state
VALID_PHASES = {"Ligue", "Plays-off", "8èmes", "Quart-finale", "Demi-finale", "Finale"}
VALID_STATES = {"En cours", "Fini", "En attente"}

# SQLAlchemy model for the odds table
class Odds(Base):
    __tablename__ = "odds"

    id = Column(Integer, primary_key=True, index=True)
    time = Column(DateTime, nullable=False)
    phase = Column(String, nullable=False)
    goals1 = Column(Integer, nullable=False)
    goals2 = Column(Integer, nullable=False)
    state = Column(String, nullable=False)
    odds1 = Column(Float, nullable=False)
    odds2 = Column(Float, nullable=False)
    oddsx = Column(Float, nullable=False)
# Automatically create the odds table
Base.metadata.create_all(bind=engine)

# Dependency to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic models for request and response validation
class OddsCreate(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    time: datetime
    phase: str
    goals1: int
    goals2: int
    state: str
    odds1: float
    odds2: float
    oddsx: float

class OddsResponse(BaseModel):
    id: int
    time: datetime
    phase: str
    goals1: int
    goals2: int
    state: str
    odds1: float
    odds2: float
    oddsx: float

    class Config:
        orm_mode = True

class OddsUpdate(BaseModel):
    time: Optional[datetime] = None
    phase: Optional[str] = None
    goals1: Optional[int] = None
    goals2: Optional[int] = None
    state: Optional[str] = None
    odds1: Optional[float] = None
    odds2: Optional[float] = None
    oddsx: Optional[float] = None

# ✅ Create a new Odds entry
@app.post("/odds/add", response_model=OddsResponse)
def create_odds(odds: OddsCreate, db: Session = Depends(get_db)):
    # Validate phase and state
    if odds.phase not in VALID_PHASES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Phase non reconnue: '{odds.phase}'. Les phases valides sont: {', '.join(VALID_PHASES)}."
            )
        )
    if odds.state not in VALID_STATES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"State non reconnu: '{odds.state}'. Les states valides sont: {', '.join(VALID_STATES)}."
            )
        )

    try:
        # Create the new odds entry
        new_odds = Odds(**odds.dict())
        db.add(new_odds)
        db.commit()
        db.refresh(new_odds)
        return new_odds
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Une erreur est survenue: {str(e)}")

# ✅ Get all odds
@app.get("/odds/all", response_model=list[OddsResponse])
def read_odds(db: Session = Depends(get_db)):
    try:
        odds = db.query(Odds).all()
        return odds
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

# ✅ Get odds by ID
@app.get("/odds/{odds_id}", response_model=OddsResponse)
def read_odds_by_id(odds_id: int, db: Session = Depends(get_db)):
    odds = db.query(Odds).filter(Odds.id == odds_id).first()
    if not odds:
        raise HTTPException(status_code=404, detail="Odds not found")
    return odds

#  Update a specific odds entry by ID
@app.put("/odds/update/{odds_id}", response_model=OddsResponse)
def update_odds(odds_id: int, odds_data: OddsUpdate, db: Session = Depends(get_db)):
    try:
        odds = db.query(Odds).filter(Odds.id == odds_id).first()
        if not odds:
            raise HTTPException(status_code=404, detail=f"Odds with ID {odds_id} not found")

        updates = odds_data.dict(exclude_unset=True)
        if not updates:
            raise HTTPException(status_code=400, detail="At least one field must be provided for update")

        if "phase" in updates and updates["phase"] not in VALID_PHASES:
            raise HTTPException(status_code=400, detail=f"Invalid phase: {updates['phase']}")
        if "state" in updates and updates["state"] not in VALID_STATES:
            raise HTTPException(status_code=400, detail=f"Invalid state: {updates['state']}")

        for field, value in updates.items():
            setattr(odds, field, value)

        db.commit()
        db.refresh(odds)
        return odds
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

# ✅ Delete a specific odds entry by ID
@app.delete("/odds/delete/{odds_id}")
def delete_odds(odds_id: int, db: Session = Depends(get_db)):
    odds = db.query(Odds).filter(Odds.id == odds_id).first()
    if not odds:
        raise HTTPException(status_code=404, detail="Odds not found")
    db.delete(odds)
    db.commit()
    return {"message": "Odds deleted successfully"}

# ✅ Update the state
async def update_odds_status():
    while True:
        try:
            db = SessionLocal()
            current_time = datetime.now()
            cutoff_time = current_time - timedelta(hours=1, minutes=45)
            
            # Print current time and cutoff time for debugging
            print(f"\n=== Status Check at {current_time.strftime('%Y-%m-%d %H:%M:%S')} ===")
            print(f"Cutoff time: {cutoff_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Update matches that should be "En attente" (future matches)
            future_matches = db.query(Odds).filter(
                Odds.time > current_time,
                Odds.state != "En attente"
            ).all()
            
            if future_matches:
                print(f"Found {len(future_matches)} future matches to set as 'En attente':")
                for odds in future_matches:
                    print(f"- Updating ID {odds.id}: Match time {odds.time.strftime('%Y-%m-%d %H:%M:%S')} -> Status: {odds.state} → En attente")
                    odds.state = "En attente"
                
            # Update matches that should be "En cours" (between start time and cutoff time)
            current_matches = db.query(Odds).filter(
                Odds.time <= current_time,
                Odds.time > cutoff_time,
                Odds.state != "En cours"
            ).all()
            
            if current_matches:
                print(f"Found {len(current_matches)} matches to set as 'En cours':")
                for odds in current_matches:
                    print(f"- Updating ID {odds.id}: Match time {odds.time.strftime('%Y-%m-%d %H:%M:%S')} -> Status: {odds.state} → En cours")
                    odds.state = "En cours"
            
            # Update matches that should be "Fini" (past cutoff time)
            finished_matches = db.query(Odds).filter(
                Odds.time <= cutoff_time,
                Odds.state != "Fini"
            ).all()
            
            if finished_matches:
                print(f"Found {len(finished_matches)} matches to set as 'Fini':")
                for odds in finished_matches:
                    print(f"- Updating ID {odds.id}: Match time {odds.time.strftime('%Y-%m-%d %H:%M:%S')} -> Status: {odds.state} → Fini")
                    odds.state = "Fini"
            
            if any([future_matches, current_matches, finished_matches]):
                db.commit()
                print("All updates committed successfully")
            else:
                print("No entries need updating")
            
        except Exception as e:
            print(f"Error updating odds status: {str(e)}")
        
        finally:
            db.close()
        
        # Wait for 10 seconds before the next check
        await asyncio.sleep(10)

# Start the background task when the application starts
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(update_odds_status())
