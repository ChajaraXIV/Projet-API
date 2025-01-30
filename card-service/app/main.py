from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import Column, Integer, String, BigInteger, Date, create_engine
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from dotenv import load_dotenv
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

# Dependency to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# SQLAlchemy model for the database table
Base = declarative_base()

class Card(Base):
    __tablename__ = "card"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    numbers = Column(BigInteger, nullable=False)
    card_type = Column(String, nullable=False)
    validity = Column(Date, nullable=False)
    crypto = Column(Integer, nullable=False)

# Pydantic models for request and response validation
class CardCreate(BaseModel):
    numbers: int
    full_name: str
    card_type: str
    validity: datetime
    crypto: int

class CardResponse(BaseModel):
    id: int
    numbers: int
    full_name: str
    card_type: str
    validity: datetime
    crypto: int

    class Config:
        orm_mode = True

class CardUpdate(BaseModel):
    numbers: Optional[int] = None
    full_name: Optional[str] = None 
    card_type: Optional[str] = None
    validity: Optional[datetime] = None
    crypto: Optional[int] = None

    class Config:
        orm_mode = True


@app.get("/")
def read_root():
    return {"message": "Welcome to the Card Service"}

# Create a new card
@app.post("/cards/add", response_model=CardResponse)
def create_card(card: CardCreate, db: Session = Depends(get_db)):
    # Validation des contraintes
    if len(str(card.numbers)) != 16 or not str(card.numbers).isdigit():
        raise HTTPException(
            status_code=400,
            detail="Card number must be a 16-digit numeric value."
        )
    
    if len(str(card.crypto)) != 3 or not str(card.crypto).isdigit():
        raise HTTPException(
            status_code=400,
            detail="Crypto must be a 3-digit numeric value."
        )
    
    if card.validity <= datetime.now():
        raise HTTPException(
            status_code=400,
            detail="Validity date must be in the future."
        )
    
    valid_card_types = {"Visa", "Mastercard", "Amex", "Discover"}
    if card.card_type not in valid_card_types:
        raise HTTPException(
            status_code=400,
            detail=f"Card type must be one of {valid_card_types}."
        )

    # Création d'une nouvelle carte
    new_card = Card(
        numbers=card.numbers,
        full_name=card.full_name,
        card_type=card.card_type,
        validity=card.validity,
        crypto=card.crypto
    )
    db.add(new_card)
    db.commit()
    db.refresh(new_card)
    return new_card

# Get all cards
@app.get("/cards/all", response_model=list[CardResponse])
def read_cards(db: Session = Depends(get_db)):
    try:
        cards = db.query(Card).all()
        return cards
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

# Get a specific card by ID
@app.get("/cards/{card_id}", response_model=CardResponse)
def read_card(card_id: int, db: Session = Depends(get_db)):
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    return card

# Update an existing card
@app.put("/cards/update/{card_id}", response_model=CardResponse)
def update_card(card_id: int, card_update: CardUpdate, db: Session = Depends(get_db)):
    # Récupération de la carte existante
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    # Mise à jour avec validation
    if card_update.numbers is not None:
        if len(str(card_update.numbers)) != 16 or not str(card_update.numbers).isdigit():
            raise HTTPException(
                status_code=400,
                detail="Card number must be a 16-digit numeric value."
            )
        card.numbers = card_update.numbers

    if card_update.full_name is not None:
        card.full_name = card_update.full_name

    if card_update.card_type is not None:
        valid_card_types = {"Visa", "Mastercard", "Amex", "Discover"}
        if card_update.card_type not in valid_card_types:
            raise HTTPException(
                status_code=400,
                detail=f"Card type must be one of {valid_card_types}."
            )
        card.card_type = card_update.card_type

    if card_update.validity is not None:
        if card_update.validity <= datetime.now():
            raise HTTPException(
                status_code=400,
                detail="Validity date must be in the future."
            )
        card.validity = card_update.validity

    if card_update.crypto is not None:
        if len(str(card_update.crypto)) != 3 or not str(card_update.crypto).isdigit():
            raise HTTPException(
                status_code=400,
                detail="Crypto must be a 3-digit numeric value."
            )
        card.crypto = card_update.crypto

    db.commit()
    db.refresh(card)
    return card
# Delete a specific card by ID
@app.delete("/cards/delete/{card_id}")
def delete_card(card_id: int, db: Session = Depends(get_db)):
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    db.delete(card)
    db.commit()
    return {"message": "Card deleted successfully"}
