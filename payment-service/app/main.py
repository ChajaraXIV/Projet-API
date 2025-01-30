from zoneinfo import ZoneInfo
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import Column, Integer, String, Float, create_engine, DateTime
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, ConfigDict
from dotenv import load_dotenv
from typing import Optional
from datetime import datetime

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
    time = Column(DateTime, nullable=False)
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
    model_config = ConfigDict(arbitrary_types_allowed=True)
    user_name: str
    amount: float
    payment_type: str

class PaymentResponse(BaseModel):
    id: int
    user_name: str
    amount: float
    payment_type: str
    time: datetime


    class Config:
        orm_mode = True

class PaymentUpdate(BaseModel):
    id: Optional[int] = None
    user_name: Optional[str] = None
    amount: Optional[float] = None
    payment_type: Optional[str] = None
    time: Optional[datetime]= None




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
                "Les types valides sont: 'depot', 'pari', 'retrait', 'gains', 'pertes'."
            )
        )

    # Validate the amount based on the payment_type
    if payment.payment_type == "depot" and not (10 < payment.amount < 100000):
        raise HTTPException(
            status_code=400,
            detail="Pour 'depot', le montant doit être supérieur à 10 et inférieur à 100000."
        )
    if payment.payment_type == "retrait" and not (10 < payment.amount < 200000):
        raise HTTPException(
            status_code=400,
            detail="Pour 'retrait', le montant doit être supérieur à 10 et inférieur à 200000."
        )
    if payment.payment_type == "pari" and not (0.1 < payment.amount < 30000):
        raise HTTPException(
            status_code=400,
            detail="Pour 'pari', le montant doit être supérieur à 10 et inférieur à 30000."
        )
    if payment.payment_type == "gains" and not (payment.amount < 200000):
        raise HTTPException(
            status_code=400,
            detail="Pour 'gains', le montant doit être inférieur à 200000."
        )
    if payment.payment_type == "pertes" and not (payment.amount < 30000):
        raise HTTPException(
            status_code=400,
            detail="Pour 'pertes', le montant doit être inférieur à 30000."
        )

    current_time = datetime.now(ZoneInfo("Europe/Paris"))
    try:
        # Create the new payment entry
        new_payment = Payment(
        user_name = payment.user_name,
        amount = payment.amount,
        payment_type = payment.payment_type,
        time = current_time
        )
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

        # Vérifier si aucun champ n'a été fourni
        updates = payment_data.dict(exclude_unset=True)
        if not updates:
            raise HTTPException(status_code=400, detail="At least one field must be provided for update")

        # Vérifier si l'utilisateur tente de modifier l'ID
        if "id" in updates:
            raise HTTPException(status_code=400, detail="Modification of 'id' is not allowed")
        
        # Vérifier les contraintes sur le montant en fonction du type de paiement
        if "payment_type" in updates or "amount" in updates:
            new_payment_type = updates.get("payment_type", payment.payment_type)
            new_amount = updates.get("amount", payment.amount)

            # Vérification des contraintes
            if new_payment_type == "depot" and not (10 < new_amount < 100000):
                raise HTTPException(status_code=400, detail="For 'depot', amount must be greater than 10 and less than 100000")
            if new_payment_type == "retrait" and not (10 < new_amount < 200000):
                raise HTTPException(status_code=400, detail="For 'retrait', amount must be greater than 10 and less than 200000")
            if new_payment_type == "pari" and not (0.1 < new_amount < 30000):
                raise HTTPException(status_code=400, detail="For 'pari', amount must be greater than 10 and less than 30000")
            if new_payment_type == "gains" and not (new_amount < 200000):
                raise HTTPException(status_code=400, detail="For 'gains', amount must be less than 200000")
            if new_payment_type == "pertes" and not (new_amount < 30000):
                raise HTTPException(status_code=400, detail="For 'pertes', amount must be less than 30000")

        # Vérifier le type de paiement s'il est envoyé
        if "payment_type" in updates and new_payment_type not in VALID_PAYMENT_TYPES:
            raise HTTPException(status_code=400, detail=f"Invalid payment_type: {new_payment_type}")

        # Mettre à jour uniquement les champs spécifiés
        for field, value in updates.items():
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