from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import Column, Integer, String, Float, create_engine
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in the environment variables")

# Initialize database engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# SQLAlchemy model for the database table
Base = declarative_base()

class Betting(Base):
    __tablename__ = "bettings"

    id = Column(Integer, primary_key=True, index=True)
    match = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    odds = Column(Float, nullable=False)

# Pydantic models for request and response validation
class BettingCreate(BaseModel):
    match: str
    amount: float
    odds: float

class BettingResponse(BaseModel):
    id: int
    match: str
    amount: float
    odds: float

    class Config:
        orm_mode = True

# Initialize FastAPI app
app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Welcome to the Betting Service"}

# Create a new betting
@app.post("/bettings/add", response_model=BettingResponse)
def create_betting(betting: BettingCreate, db: Session = Depends(get_db)):
    try:
        new_betting = Betting(**betting.dict())
        db.add(new_betting)
        db.commit()
        db.refresh(new_betting)
        return new_betting
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

# Get all bettings
@app.get("/bettings/all", response_model=list[BettingResponse])
def read_bettings(db: Session = Depends(get_db)):
    try:
        bettings = db.query(Betting).all()
        return bettings
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

# Get a specific betting by ID
@app.get("/bettings/{betting_id}", response_model=BettingResponse)
def read_betting(betting_id: int, db: Session = Depends(get_db)):
    betting = db.query(Betting).filter(Betting.id == betting_id).first()
    if not betting:
        raise HTTPException(status_code=404, detail="Betting not found")
    return betting

# Update a specific betting by ID
@app.put("/bettings/update/{betting_id}", response_model=BettingResponse)
def update_betting(betting_id: int, updated_betting: BettingCreate, db: Session = Depends(get_db)):
    betting = db.query(Betting).filter(Betting.id == betting_id).first()
    if not betting:
        raise HTTPException(status_code=404, detail="Betting not found")
    for key, value in updated_betting.dict().items():
        setattr(betting, key, value)
    db.commit()
    db.refresh(betting)
    return betting

# Delete a specific betting by ID
@app.delete("/bettings/delete/{betting_id}")
def delete_betting(betting_id: int, db: Session = Depends(get_db)):
    betting = db.query(Betting).filter(Betting.id == betting_id).first()
    if not betting:
        raise HTTPException(status_code=404, detail="Betting not found")
    db.delete(betting)
    db.commit()
    return {"message": "Betting deleted successfully"}
