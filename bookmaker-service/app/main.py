from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import Column, Integer, String, create_engine
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

# Create the Base for SQLAlchemy models
Base = declarative_base()

# SQLAlchemy model for the bookmakers table
class Bookmaker(Base):
    __tablename__ = "bookmakers"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)

# Automatically create the bookmakers table
Base.metadata.create_all(bind=engine)

# Dependency to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic models for request and response validation
class BookmakerCreate(BaseModel):
    first_name: str
    last_name: str

class BookmakerResponse(BaseModel):
    id: int
    first_name: str
    last_name: str

    class Config:
        orm_mode = True

# ✅ Create a new Bookmaker
@app.post("/bookmakers/add", response_model=BookmakerResponse)
def create_bookmaker(bookmaker: BookmakerCreate, db: Session = Depends(get_db)):
    try:
        new_bookmaker = Bookmaker(**bookmaker.dict())
        db.add(new_bookmaker)
        db.commit()
        db.refresh(new_bookmaker)
        return new_bookmaker
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Une erreur est survenue: {str(e)}")

# ✅ Get all bookmakers
@app.get("/bookmakers/all", response_model=list[BookmakerResponse])
def read_bookmakers(db: Session = Depends(get_db)):
    try:
        bookmakers = db.query(Bookmaker).all()
        return bookmakers
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

# ✅ Get bookmaker by ID
@app.get("/bookmakers/{bookmaker_id}", response_model=BookmakerResponse)
def read_bookmaker(bookmaker_id: int, db: Session = Depends(get_db)):
    bookmaker = db.query(Bookmaker).filter(Bookmaker.id == bookmaker_id).first()
    if not bookmaker:
        raise HTTPException(status_code=404, detail="Bookmaker not found")
    return bookmaker

# ✅ Delete a bookmaker
@app.delete("/bookmakers/delete/{bookmaker_id}")
def delete_bookmaker(bookmaker_id: int, db: Session = Depends(get_db)):
    bookmaker = db.query(Bookmaker).filter(Bookmaker.id == bookmaker_id).first()
    if not bookmaker:
        raise HTTPException(status_code=404, detail="Bookmaker not found")
    db.delete(bookmaker)
    db.commit()
    return {"message": "Bookmaker deleted successfully"}
