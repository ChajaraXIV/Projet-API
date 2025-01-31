import os
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Union

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

# Types de paris valides
VALID_ODDS_TYPE = {"Simple", "Combine"}

# Modèles Pydantic
class BettingCreate(BaseModel):
    user_id: int
    match_ids: Union[int, List[int]]  # Accepte un seul match ou plusieurs matchs
    odds: Union[float, List[float]]  # Accepte une seule cote ou plusieurs
    amount: float  # Montant total pour le pari
    odds_type: Optional[str] = None   # 'Simple' ou 'Combine'

class BettingUpdate(BaseModel):
    user_id: int
    match_id: int
    amount: float
    odds: float
    odds_type: str

# ✅ Route de test
@app.get("/")
def read_root():
    return {"message": "Welcome to Betting Service"}

@app.post("/bets/add")
def add_bet(bet: BettingCreate):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Vérification de l'existence de l'utilisateur
        cur.execute("SELECT id FROM users WHERE id = %s", (bet.user_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

        # Gérer le cas du pari simple ou combiné automatiquement
        if isinstance(bet.match_ids, int):  # 🟢 Cas pari simple
            match_ids = [bet.match_ids]  # Convertir en liste
            odds_list = [bet.odds]
            bet.odds_type = "Simple"  # Auto-set en Simple
        else:  # 🔴 Cas pari combiné
            match_ids = bet.match_ids
            odds_list = bet.odds
            bet.odds_type = "Combine"  # Auto-set en Combine

        # Vérification des matchs et validation des cotes
        total_odds = 1
        for match_id, odd in zip(match_ids, odds_list):
            cur.execute("SELECT odds1, odds2, oddsx FROM odds WHERE id = %s", (match_id,))
            result = cur.fetchone()
            if not result:
                raise HTTPException(status_code=404, detail=f"Match ID {match_id} non trouvé")

            odds1, odds2, oddsx = result["odds1"], result["odds2"], result["oddsx"]

            # Vérifier que la cote choisie est bien une cote valide du match
            if odd not in [odds1, odds2, oddsx]:
                raise HTTPException(status_code=400, detail=f"La cote {odd} n'est pas valide pour le match {match_id}")

            total_odds *= odd  # Multiplication des cotes pour un pari combiné

        # Calcul des gains potentiels
        winnings = bet.amount * total_odds

        # Stocker `match_ids` sous forme de string pour garder l'historique
        match_ids_str = ",".join(map(str, match_ids))
        odds_str = ",".join(map(str, odds_list))

        # Insertion du pari dans `bets`
        cur.execute(
            """
            INSERT INTO bets (user_id, match_ids, amount, odds_list, odds, odds_type, time, winnings)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
            """,
            (bet.user_id, match_ids_str, bet.amount, odds_str, total_odds, bet.odds_type, datetime.now(), winnings)
        )
        bet_id = cur.fetchone()["id"]

        conn.commit()
        return {"message": "Pari ajouté avec succès", "bet_id": bet_id, "odds_type": bet.odds_type}

    except psycopg2.IntegrityError:
        conn.rollback()
        raise HTTPException(status_code=400, detail="Erreur d'intégrité (vérifie user_id et match_id).")
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

# ✅ Obtenir tous les paris
@app.get("/bets/all")
def get_all_bets():
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT * FROM bets ORDER BY time DESC")
        bets = cur.fetchall()

        if not bets:
            raise HTTPException(status_code=404, detail="Aucun pari trouvé")

        return {"bets": bets}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

# ✅ Obtenir un pari par ID
@app.get("/bets/{bet_id}")
def get_bet(bet_id: int):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT * FROM bets WHERE id = %s", (bet_id,))
        bet = cur.fetchone()

        if not bet:
            raise HTTPException(status_code=404, detail="Pari non trouvé")

        return bet

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

# ✅ Supprimer un pari
@app.delete("/bets/delete/{bet_id}")
def delete_bet(bet_id: int):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Vérification si le pari existe
        cur.execute("SELECT id FROM bets WHERE id = %s", (bet_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Pari non trouvé")

        # Suppression du pari
        cur.execute("DELETE FROM bets WHERE id = %s", (bet_id,))
        conn.commit()

        return {"message": "Bet deleted successfully"}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()
