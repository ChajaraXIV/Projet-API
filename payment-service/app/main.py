from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import Column, Integer, String, Float, create_engine
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

# SQLAlchemy model for the payments table
class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    payment_type = Column(String, nullable=False)

# Automatically create the payments table
Base.metadata.create_all(bind=engine)

# Dependency to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic models for request and response validation
class PaymentCreate(BaseModel):
    user_name: str
    amount: float
    payment_type: str

class PaymentResponse(BaseModel):
    id: int
    user_name: str
    amount: float
    payment_type: str

    class Config:
        orm_mode = True



class PaymentUpdate(BaseModel):
    user_name: str
    amount: float
    payment_type: str

VALID_PAYMENT_TYPES = {"depot", "pari", "retrait","gains","pertes"}

# Initialize FastAPI app
app = FastAPI()

@app.get("/")
def read_root():
    return {"Fen": "zabi"}



# # ✅ Create a new Payment
@app.post("/payments/add", response_model=PaymentResponse)
def create_payment(payment: PaymentCreate, db: Session = Depends(get_db)):
    # Validate the payment_type against the allowed values
    if payment.payment_type not in VALID_PAYMENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Type de paiement non reconnu: '{payment.payment_type}'. "
                "Les types valides sont: 'depot', 'pari', 'retrait','gains','pertes'."
            )
        )
    try:
        new_payment = Payment(**payment.dict())
        db.add(new_payment)
        db.commit()
        db.refresh(new_payment)
        return new_payment
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Une erreur est survenue: {str(e)}")

# ✅Get all payments
@app.get("/payments/all", response_model=list[PaymentResponse])
def read_payments(db: Session = Depends(get_db)):
    try:
        payments = db.query(Payment).all()
        return payments
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

# ✅Get payment from id
@app.get("/payments/{payment_id}",response_model=PaymentResponse)
def read_payment(payment_id: int, db: Session = Depends(get_db)):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment

# ✅Update a specific payment by ID
@app.put("/payments/{payment_id}", response_model=PaymentResponse)
def update_payment(payment_id: int, payment_data: PaymentUpdate, db: Session = Depends(get_db)):
    try:
        # Récupérer le paiement existant
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            raise HTTPException(status_code=404, detail=f"Payment with ID {payment_id} not found")
        
        # Mettre à jour les champs spécifiés
        for field, value in payment_data.dict(exclude_unset=True).items():
            setattr(payment, field, value)
        
        # Enregistrer les changements dans la base de données
        db.commit()
        db.refresh(payment)
        
        return payment
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

# ✅Delete a specific payment by ID
@app.delete("/payments/delete/{payment_id}")
def delete_betting(payment_id: int, db: Session = Depends(get_db)):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    db.delete(payment)
    db.commit()
    return {"message": "Payment deleted successfully"}

@app.get("/jad")
def read_root():
    return {"Fen": "zabi"}