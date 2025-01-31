import os
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime

# Initialisation de FastAPI
app = FastAPI()

# Configuration de la base de données
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_NAME = os.getenv("DB_NAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Connexion à PostgreSQL
def get_db_connection():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=5432,
        cursor_factory=RealDictCursor
    )

# Modèle Pydantic pour la création et la mise à jour des paiements
class PaymentCreate(BaseModel):
    user_id: int
    amount: float
    payment_type: str

class PaymentUpdate(BaseModel):
    user_id: int
    amount: float
    payment_type: str

# Liste des types de paiement valides
VALID_PAYMENT_TYPES = {"depot", "pari", "retrait", "gains", "pertes"}

# ✅ Route de test
@app.get("/")
def read_root():
    return {"message": "Welcome to Payment Service"}

# ✅ Ajouter un paiement avec validation complète
@app.post("/payments/add")
def add_payment(payment: PaymentCreate):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Vérification du type de paiement
        if payment.payment_type not in VALID_PAYMENT_TYPES:
            raise HTTPException(status_code=400, detail=f"Type de paiement invalide: {payment.payment_type}")

        # Vérification des contraintes de montant
        if payment.payment_type == "depot" and not (10 < payment.amount < 100000):
            raise HTTPException(status_code=400, detail="Pour 'depot', le montant doit être entre 10 et 100000.")
        if payment.payment_type == "retrait" and not (10 < payment.amount < 200000):
            raise HTTPException(status_code=400, detail="Pour 'retrait', le montant doit être entre 10 et 200000.")
        if payment.payment_type == "pari" and not (0.1 < payment.amount < 30000):
            raise HTTPException(status_code=400, detail="Pour 'pari', le montant doit être entre 0.1 et 30000.")
        if payment.payment_type == "gains" and payment.amount >= 200000:
            raise HTTPException(status_code=400, detail="Pour 'gains', le montant doit être inférieur à 200000.")
        if payment.payment_type == "pertes" and payment.amount >= 30000:
            raise HTTPException(status_code=400, detail="Pour 'pertes', le montant doit être inférieur à 30000.")

        # Insertion dans la base de données
        cur.execute(
            """
            INSERT INTO payments (user_id, amount, payment_type, time)
            VALUES (%s, %s, %s, %s) RETURNING id
            """,
            (payment.user_id, payment.amount, payment.payment_type, datetime.now())
        )
        payment_id = cur.fetchone()["id"]
        conn.commit()

        return {"message": "Payment added successfully", "payment_id": payment_id}

    except psycopg2.IntegrityError:
        conn.rollback()
        raise HTTPException(status_code=400, detail="Erreur d'intégrité (vérifie l'existence de l'user_id).")
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

# ✅ Mettre à jour un paiement avec validation complète
@app.put("/payments/update/{payment_id}")
def update_payment(payment_id: int, payment: PaymentUpdate):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Vérification si le paiement existe
        cur.execute("SELECT * FROM payments WHERE id = %s", (payment_id,))
        existing_payment = cur.fetchone()
        if not existing_payment:
            raise HTTPException(status_code=404, detail="Paiement non trouvé")

        # Vérification des contraintes de montant
        if payment.payment_type == "depot" and not (10 < payment.amount < 100000):
            raise HTTPException(status_code=400, detail="Pour 'depot', le montant doit être entre 10 et 100000.")
        if payment.payment_type == "retrait" and not (10 < payment.amount < 200000):
            raise HTTPException(status_code=400, detail="Pour 'retrait', le montant doit être entre 10 et 200000.")
        if payment.payment_type == "pari" and not (0.1 < payment.amount < 30000):
            raise HTTPException(status_code=400, detail="Pour 'pari', le montant doit être entre 0.1 et 30000.")
        if payment.payment_type == "gains" and payment.amount >= 200000:
            raise HTTPException(status_code=400, detail="Pour 'gains', le montant doit être inférieur à 200000.")
        if payment.payment_type == "pertes" and payment.amount >= 30000:
            raise HTTPException(status_code=400, detail="Pour 'pertes', le montant doit être inférieur à 30000.")

        # Mise à jour du paiement
        cur.execute(
            """
            UPDATE payments 
            SET user_id = %s, amount = %s, payment_type = %s, time = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (payment.user_id, payment.amount, payment.payment_type, payment_id)
        )
        conn.commit()

        return {"message": "Payment updated successfully"}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

# ✅ Supprimer un paiement
@app.delete("/payments/delete/{payment_id}")
def delete_payment(payment_id: int):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Vérifier si le paiement existe
        cur.execute("SELECT id FROM payments WHERE id = %s", (payment_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Paiement non trouvé")

        # Suppression du paiement
        cur.execute("DELETE FROM payments WHERE id = %s", (payment_id,))
        conn.commit()

        return {"message": "Payment deleted successfully"}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

# ✅ Obtenir tous les paiements
@app.get("/payments/all")
def get_all_payments():
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT * FROM payments ORDER BY time DESC")
        payments = cur.fetchall()
        
        if not payments:
            raise HTTPException(status_code=404, detail="Aucun paiement trouvé")
        
        return {"payments": payments}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

@app.get("/payments/{payment_id}")
def get_payment(payment_id: int):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT * FROM payments WHERE id = %s", (payment_id,))
        payment = cur.fetchone()

        if not payment:
            raise HTTPException(status_code=404, detail="Paiement non trouvé")

        return payment

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()
