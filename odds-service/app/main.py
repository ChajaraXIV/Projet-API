# import asyncio
# from zoneinfo import ZoneInfo
# from fastapi import FastAPI, HTTPException, Depends
# from sqlalchemy.orm import sessionmaker, Session
# from sqlalchemy import Column, Integer, String, Float, create_engine, DateTime, Enum
# from sqlalchemy.ext.declarative import declarative_base
# from pydantic import BaseModel, ConfigDict
# from dotenv import load_dotenv
# from typing import Optional
# from datetime import datetime, timedelta
# import os

# # Initialize FastAPI app
# app = FastAPI()

# # Load environment variables
# load_dotenv()

# # Database configuration
# DATABASE_URL = os.getenv("DATABASE_URL")
# if not DATABASE_URL:
#     raise ValueError("DATABASE_URL is not set in the environment variables")

# # Initialize database engine and session
# engine = create_engine(DATABASE_URL)
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# # Create the Base for SQLAlchemy models
# Base = declarative_base()

# # Valid ENUM values for phase and state
# VALID_PHASES = {"Ligue", "Plays-off", "8èmes", "Quart-finale", "Demi-finale", "Finale"}
# VALID_STATES = {"En cours", "Fini", "En attente"}

# # SQLAlchemy model for the odds table
# class Odds(Base):
#     __tablename__ = "odds"

#     id = Column(Integer, primary_key=True, index=True)
#     time = Column(DateTime, nullable=False)
#     phase = Column(String, nullable=False)
#     goals1 = Column(Integer, nullable=False)
#     goals2 = Column(Integer, nullable=False)
#     state = Column(String, nullable=False)
#     odds1 = Column(Float, nullable=False)
#     odds2 = Column(Float, nullable=False)
#     oddsx = Column(Float, nullable=False)
# # Automatically create the odds table
# Base.metadata.create_all(bind=engine)

# # Dependency to get a database session
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

# # Pydantic models for request and response validation
# class OddsCreate(BaseModel):
#     model_config = ConfigDict(arbitrary_types_allowed=True)
#     time: datetime
#     phase: str
#     goals1: int
#     goals2: int
#     odds1: float
#     odds2: float
#     oddsx: float

# class OddsResponse(BaseModel):
#     id: int
#     time: datetime
#     phase: str
#     goals1: int
#     goals2: int
#     state: str
#     odds1: float
#     odds2: float
#     oddsx: float

#     class Config:
#         orm_mode = True

# class OddsUpdate(BaseModel):
#     time: Optional[datetime] = None
#     phase: Optional[str] = None
#     goals1: Optional[int] = None
#     goals2: Optional[int] = None
#     state: Optional[str] = None
#     odds1: Optional[float] = None
#     odds2: Optional[float] = None
#     oddsx: Optional[float] = None

# # ✅ Create a new Odds entry
# @app.post("/odds/add", response_model=OddsResponse)
# def create_odds(odds: OddsCreate, db: Session = Depends(get_db)):
#     # Determine the state based on the match time
#     current_time = datetime.now()
#     cutoff_time = current_time - timedelta(hours=1, minutes=45)

#     if odds.time > current_time:
#         calculated_state = "En attente"
#     elif cutoff_time <= odds.time <= current_time :
#         calculated_state = "En cours"
#     else:
#         calculated_state = "Fini"

#     # Validate phase
#     if odds.phase not in VALID_PHASES:
#         raise HTTPException(
#             status_code=400,
#             detail=f"Phase non reconnue: '{odds.phase}'. Les phases valides sont: {', '.join(VALID_PHASES)}."
#         )

#     try:
#         # Create the new odds entry with the calculated state
#         new_odds = Odds(
#             time=odds.time,
#             phase=odds.phase,
#             goals1=odds.goals1,
#             goals2=odds.goals2,
#             state=calculated_state,
#             odds1=odds.odds1,
#             odds2=odds.odds2,
#             oddsx=odds.oddsx
#         )

#         db.add(new_odds)
#         db.commit()
#         db.refresh(new_odds)
#         return new_odds
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Une erreur est survenue: {str(e)}")


# # ✅ Get all odds
# @app.get("/odds/all", response_model=list[OddsResponse])
# def read_odds(db: Session = Depends(get_db)):
#     try:
#         odds = db.query(Odds).all()
#         return odds
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

# # ✅ Get odds by ID
# @app.get("/odds/{odds_id}", response_model=OddsResponse)
# def read_odds_by_id(odds_id: int, db: Session = Depends(get_db)):
#     odds = db.query(Odds).filter(Odds.id == odds_id).first()
#     if not odds:
#         raise HTTPException(status_code=404, detail="Odds not found")
#     return odds

# #  Update a specific odds entry by ID
# @app.put("/odds/update/{odds_id}", response_model=OddsResponse)
# def update_odds(odds_id: int, odds_data: OddsUpdate, db: Session = Depends(get_db)):
#     try:
#         odds = db.query(Odds).filter(Odds.id == odds_id).first()
#         if not odds:
#             raise HTTPException(status_code=404, detail=f"Odds with ID {odds_id} not found")

#         updates = odds_data.dict(exclude_unset=True)
#         if not updates:
#             raise HTTPException(status_code=400, detail="At least one field must be provided for update")

#         if "phase" in updates and updates["phase"] not in VALID_PHASES:
#             raise HTTPException(status_code=400, detail=f"Invalid phase: {updates['phase']}")
#         if "state" in updates and updates["state"] not in VALID_STATES:
#             raise HTTPException(status_code=400, detail=f"Invalid state: {updates['state']}")

#         for field, value in updates.items():
#             setattr(odds, field, value)

#         db.commit()
#         db.refresh(odds)
#         return odds
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

# # ✅ Delete a specific odds entry by ID
# @app.delete("/odds/delete/{odds_id}")
# def delete_odds(odds_id: int, db: Session = Depends(get_db)):
#     odds = db.query(Odds).filter(Odds.id == odds_id).first()
#     if not odds:
#         raise HTTPException(status_code=404, detail="Odds not found")
#     db.delete(odds)
#     db.commit()
#     return {"message": "Odds deleted successfully"}

# # ✅ Update the state
# async def update_odds_status():
#     while True:
#         try:
#             db = SessionLocal()
#             current_time = datetime.now(ZoneInfo("Europe/Paris"))
#             cutoff_time = current_time - timedelta(hours=1, minutes=45)
            
#             # Print current time and cutoff time for debugging
#             print(f"\n=== Status Check at {current_time.strftime('%Y-%m-%d %H:%M:%S')} ===")
#             print(f"Cutoff time: {cutoff_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
#             # Update matches that should be "En attente" (future matches)
#             future_matches = db.query(Odds).filter(
#                 Odds.time > current_time,
#                 Odds.state != "En attente"
#             ).all()
            
#             if future_matches:
#                 print(f"Found {len(future_matches)} future matches to set as 'En attente':")
#                 for odds in future_matches:
#                     print(f"- Updating ID {odds.id}: Match time {odds.time.strftime('%Y-%m-%d %H:%M:%S')} -> Status: {odds.state} → En attente")
#                     odds.state = "En attente"
                
#             # Update matches that should be "En cours" (between start time and cutoff time)
#             current_matches = db.query(Odds).filter(
#                 Odds.time <= current_time,
#                 Odds.time > cutoff_time,
#                 Odds.state != "En cours"
#             ).all()
            
#             if current_matches:
#                 print(f"Found {len(current_matches)} matches to set as 'En cours':")
#                 for odds in current_matches:
#                     print(f"- Updating ID {odds.id}: Match time {odds.time.strftime('%Y-%m-%d %H:%M:%S')} -> Status: {odds.state} → En cours")
#                     odds.state = "En cours"
            
#             # Update matches that should be "Fini" (past cutoff time)
#             finished_matches = db.query(Odds).filter(
#                 Odds.time <= cutoff_time,
#                 Odds.state != "Fini"
#             ).all()
            
#             if finished_matches:
#                 print(f"Found {len(finished_matches)} matches to set as 'Fini':")
#                 for odds in finished_matches:
#                     print(f"- Updating ID {odds.id}: Match time {odds.time.strftime('%Y-%m-%d %H:%M:%S')} -> Status: {odds.state} → Fini")
#                     odds.state = "Fini"
            
#             if any([future_matches, current_matches, finished_matches]):
#                 db.commit()
#                 print("All updates committed successfully")
#             else:
#                 print("No entries need updating")
            
#         except Exception as e:
#             print(f"Error updating odds status: {str(e)}")
        
#         finally:
#             db.close()
        
#         # Wait for 10 seconds before the next check
#         await asyncio.sleep(10)

# # Start the background task when the application starts
# @app.on_event("startup")
# async def startup_event():
#     asyncio.create_task(update_odds_status())
import asyncio
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

# Charger les variables d'environnement
load_dotenv()

# Initialisation de FastAPI
app = FastAPI()

# Connexion à PostgreSQL
def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=5432,
        cursor_factory=RealDictCursor
    )

# Phases et États valides
VALID_PHASES = {"Ligue", "Plays-off", "8èmes", "Quart-finale", "Demi-finale", "Finale"}
VALID_STATES = {"En cours", "Fini", "En attente"}

# Modèle Pydantic pour créer un match
class OddsCreate(BaseModel):
    time: datetime
    phase: str
    team1_id: int
    team2_id: int
    goals1: int
    goals2: int
    odds1: float
    odds2: float
    oddsx: float

class OddsUpdate(BaseModel):
    time: Optional[datetime] = None
    phase: Optional[str] = None
    team1_id: Optional[int] = None
    team2_id: Optional[int] = None
    goals1: Optional[int] = None
    goals2: Optional[int] = None
    odds1: Optional[float] = None
    odds2: Optional[float] = None
    oddsx: Optional[float] = None

# ✅ Mettre à jour un match par ID avec des champs optionnels
@app.put("/odds/update/{odds_id}")
def update_odds(odds_id: int, odds_data: OddsUpdate):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Vérifier si le match existe
        cur.execute("SELECT * FROM odds WHERE id = %s", (odds_id,))
        existing_odds = cur.fetchone()

        if not existing_odds:
            raise HTTPException(status_code=404, detail="Match non trouvé.")

        # Préparer la mise à jour
        updates = {}
        if odds_data.time is not None:
            updates["time"] = odds_data.time
        if odds_data.phase is not None:
            updates["phase"] = odds_data.phase
        if odds_data.team1_id is not None:
            cur.execute("SELECT name FROM teams WHERE id = %s", (odds_data.team1_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="L'équipe 1 n'existe pas.")
            updates["team1_id"] = odds_data.team1_id
        if odds_data.team2_id is not None:
            cur.execute("SELECT name FROM teams WHERE id = %s", (odds_data.team2_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="L'équipe 2 n'existe pas.")
            updates["team2_id"] = odds_data.team2_id
        if odds_data.goals1 is not None:
            updates["goals1"] = odds_data.goals1
        if odds_data.goals2 is not None:
            updates["goals2"] = odds_data.goals2
        if odds_data.odds1 is not None:
            updates["odds1"] = odds_data.odds1
        if odds_data.odds2 is not None:
            updates["odds2"] = odds_data.odds2
        if odds_data.oddsx is not None:
            updates["oddsx"] = odds_data.oddsx

        # Déterminer l'état du match en fonction du temps si la date est modifiée
        if "time" in updates:
            current_time = datetime.now()
            cutoff_time = current_time - timedelta(hours=1, minutes=45)

            if updates["time"] > current_time:
                updates["state"] = "En attente"
            elif cutoff_time <= updates["time"] <= current_time:
                updates["state"] = "En cours"
            else:
                updates["state"] = "Fini"

        # Construire la requête SQL dynamique
        set_clause = ", ".join([f"{key} = %s" for key in updates.keys()])
        values = list(updates.values()) + [odds_id]

        sql_query = f"UPDATE odds SET {set_clause} WHERE id = %s"
        cur.execute(sql_query, values)

        conn.commit()

        return {"message": "Match mis à jour avec succès", "odds_id": odds_id}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()
        
# ✅ Ajouter un match avec des équipes
@app.post("/odds/add")
def create_odds(odds: OddsCreate):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Vérifier l'existence des équipes
        cur.execute("SELECT name FROM teams WHERE id = %s", (odds.team1_id,))
        team1 = cur.fetchone()
        cur.execute("SELECT name FROM teams WHERE id = %s", (odds.team2_id,))
        team2 = cur.fetchone()

        if not team1 or not team2:
            raise HTTPException(status_code=404, detail="L'une des équipes n'existe pas.")

        # Déterminer l'état du match
        current_time = datetime.now()
        cutoff_time = current_time - timedelta(hours=1, minutes=45)

        if odds.time > current_time:
            calculated_state = "En attente"
        elif cutoff_time <= odds.time <= current_time:
            calculated_state = "En cours"
        else:
            calculated_state = "Fini"

        # Insérer le match dans la table `odds`
        cur.execute(
            """
            INSERT INTO odds (time, phase, team1_id, team2_id, goals1, goals2, state, odds1, odds2, oddsx)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
            """,
            (odds.time, odds.phase, odds.team1_id, odds.team2_id, odds.goals1, odds.goals2,
             calculated_state, odds.odds1, odds.odds2, odds.oddsx)
        )

        odds_id = cur.fetchone()["id"]
        conn.commit()

        return {"message": "Match ajouté avec succès", "odds_id": odds_id}

    except psycopg2.IntegrityError:
        conn.rollback()
        raise HTTPException(status_code=400, detail="Erreur d'intégrité.")
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

# ✅ Fonction pour mettre à jour l'état des matchs
async def update_odds_status():
    while True:
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            current_time = datetime.now()
            cutoff_time = current_time - timedelta(hours=1, minutes=45)

            # Mettre à jour les matchs à "En attente"
            cur.execute(
                """
                UPDATE odds 
                SET state = 'En attente'
                WHERE time > %s AND state != 'En attente'
                """,
                (current_time,)
            )

            # Mettre à jour les matchs à "En cours"
            cur.execute(
                """
                UPDATE odds 
                SET state = 'En cours'
                WHERE time <= %s AND time > %s AND state != 'En cours'
                """,
                (current_time, cutoff_time)
            )

            # Mettre à jour les matchs à "Fini"
            cur.execute(
                """
                UPDATE odds 
                SET state = 'Fini'
                WHERE time <= %s AND state != 'Fini'
                """,
                (cutoff_time,)
            )

            conn.commit()
            print(f"[{datetime.now()}] Mise à jour des états des matchs terminée.")

        except Exception as e:
            print(f"Erreur lors de la mise à jour des états des matchs: {str(e)}")

        finally:
            cur.close()
            conn.close()

        await asyncio.sleep(10)  # Vérification toutes les 10 secondes

# Lancer la tâche de mise à jour des états des matchs
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(update_odds_status())

# ✅ Obtenir tous les matchs avec les noms des équipes
@app.get("/odds/all")
def read_odds():
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT o.id, o.time, o.phase, 
                   t1.name AS team1_name, t2.name AS team2_name, 
                   o.goals1, o.goals2, o.state, o.odds1, o.odds2, o.oddsx
            FROM odds o
            JOIN teams t1 ON o.team1_id = t1.id
            JOIN teams t2 ON o.team2_id = t2.id
            ORDER BY o.time DESC
            """
        )
        odds_list = cur.fetchall()

        if not odds_list:
            raise HTTPException(status_code=404, detail="Aucun match trouvé.")

        return {"odds": odds_list}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

# # ✅ Mettre à jour un match par ID
# @app.put("/odds/update/{odds_id}")
# def update_odds(odds_id: int, odds_data: OddsCreate):
#     conn = get_db_connection()
#     cur = conn.cursor()

#     try:
#         # Vérifier si le match existe
#         cur.execute("SELECT id FROM odds WHERE id = %s", (odds_id,))
#         if not cur.fetchone():
#             raise HTTPException(status_code=404, detail="Match non trouvé.")

#         # Vérifier l'existence des équipes
#         cur.execute("SELECT name FROM teams WHERE id = %s", (odds_data.team1_id,))
#         team1 = cur.fetchone()
#         cur.execute("SELECT name FROM teams WHERE id = %s", (odds_data.team2_id,))
#         team2 = cur.fetchone()

#         if not team1 or not team2:
#             raise HTTPException(status_code=404, detail="L'une des équipes n'existe pas.")

#         # Déterminer l'état du match en fonction du temps
#         current_time = datetime.now()
#         cutoff_time = current_time - timedelta(hours=1, minutes=45)

#         if odds_data.time > current_time:
#             new_state = "En attente"
#         elif cutoff_time <= odds_data.time <= current_time:
#             new_state = "En cours"
#         else:
#             new_state = "Fini"

#         # Mettre à jour le match dans la table `odds`
#         cur.execute(
#             """
#             UPDATE odds
#             SET time = %s, phase = %s, team1_id = %s, team2_id = %s, 
#                 goals1 = %s, goals2 = %s, state = %s, odds1 = %s, odds2 = %s, oddsx = %s
#             WHERE id = %s
#             """,
#             (odds_data.time, odds_data.phase, odds_data.team1_id, odds_data.team2_id,
#              odds_data.goals1, odds_data.goals2, new_state, odds_data.odds1, odds_data.odds2, odds_data.oddsx, odds_id)
#         )

#         conn.commit()

#         return {"message": "Match mis à jour avec succès", "odds_id": odds_id}

#     except Exception as e:
#         conn.rollback()
#         raise HTTPException(status_code=500, detail=str(e))
#     finally:
#         cur.close()
#         conn.close()

# ✅ Obtenir un match par ID
@app.get("/odds/{odds_id}")
def read_odds_by_id(odds_id: int):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT o.id, o.time, o.phase, 
                   t1.name AS team1_name, t2.name AS team2_name, 
                   o.goals1, o.goals2, o.state, o.odds1, o.odds2, o.oddsx
            FROM odds o
            JOIN teams t1 ON o.team1_id = t1.id
            JOIN teams t2 ON o.team2_id = t2.id
            WHERE o.id = %s
            """,
            (odds_id,)
        )
        odds = cur.fetchone()

        if not odds:
            raise HTTPException(status_code=404, detail="Match non trouvé.")

        return odds

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()
