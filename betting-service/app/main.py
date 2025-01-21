from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import Column, Integer, String, Float, DateTime, create_engine
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

VALID_ODDS_TYPE = {"Simple", "Combine"}

class Bets(Base):
    __tablename__ = "bets"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    odds = Column(Float, nullable=False)
    odds_type = Column(String, nullable=False)
    time = Column(DateTime, default=datetime.utcnow, nullable=False)
    winnings = Column(Float, nullable=False)

# Pydantic models for request and response validation
class BettingCreate(BaseModel):
    amount: float
    odds: float
    odds_type: str

class BettingResponse(BaseModel):
    id: int
    amount: float
    odds: float
    odds_type: str
    time: datetime
    winnings: float

    class Config:
        orm_mode = True

# Pydantic model for updating a betting
class BettingUpdate(BaseModel):
    amount: Optional[float] = None
    odds: Optional[float] = None
    odds_type: Optional[str] = None

    class Config:
        orm_mode = True

# Initialize FastAPI app
app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Welcome to the Betting Service"}

# Create a new betting
@app.post("/bets/add", response_model=BettingResponse)
def create_bet(bet: BettingCreate, db: Session = Depends(get_db)):
    # Validate odds_type
    if bet.odds_type not in VALID_ODDS_TYPE:
        raise HTTPException(status_code=400, detail="Invalid odds_type. Must be 'Simple' or 'Combine'.")

    # Calculate winnings and current time
    winnings = bet.amount * bet.odds
    time = datetime.now()

    # Create new bet record
    new_bet = Bets(
        amount=bet.amount,
        odds=bet.odds,
        odds_type=bet.odds_type,
        time=time,
        winnings=winnings
    )
    db.add(new_bet)
    db.commit()
    db.refresh(new_bet)

    return new_bet


# Get all betting
@app.get("/bets/all", response_model=list[BettingResponse])
def read_betting(db: Session = Depends(get_db)):
    try:
        bettings = db.query(Bets).all()
        return bettings
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

# Get a specific betting by ID
@app.get("/bets/{bets_id}", response_model=BettingResponse)
def read_betting(bets_id: int, db: Session = Depends(get_db)):
    betting = db.query(Bets).filter(Bets.id == bets_id).first()
    if not betting:
        raise HTTPException(status_code=404, detail="Betting not found")
    return betting

# Update an existing betting
@app.put("/bets/update/{bets_id}", response_model=BettingResponse)
def update_bet(bets_id: int, bet_update: BettingUpdate, db: Session = Depends(get_db)):
    # Retrieve the existing bet
    bet = db.query(Bets).filter(Bets.id == bets_id).first()
    if not bet:
        raise HTTPException(status_code=404, detail="Betting not found")

    # Update the bet attributes
    if bet_update.amount is not None:
        bet.amount = bet_update.amount

    if bet_update.odds is not None:
        bet.odds = bet_update.odds

    if bet_update.odds_type is not None:
        if bet_update.odds_type not in VALID_ODDS_TYPE:
            raise HTTPException(status_code=400, detail="Invalid odds_type. Must be 'Simple' or 'Combine'.")
        bet.odds_type = bet_update.odds_type

    # Recalculate winnings if amount or odds changed
    if bet_update.amount is not None or bet_update.odds is not None:
        bet.winnings = bet.amount * bet.odds

    # Commit the changes to the database
    db.commit()
    db.refresh(bet)

    return bet


# Delete a specific betting by ID
@app.delete("/bets/delete/{betting_id}")
def delete_betting(betting_id: int, db: Session = Depends(get_db)):
    betting = db.query(Bets).filter(Bets.id == betting_id).first()
    if not betting:
        raise HTTPException(status_code=404, detail="Betting not found")
    db.delete(betting)
    db.commit()
    return {"message": "Betting deleted successfully"}
