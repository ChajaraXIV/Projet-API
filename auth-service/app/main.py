from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel, EmailStr
from passlib.hash import bcrypt
from datetime import datetime, timedelta
import jwt
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os

# Initialisation de FastAPI
app = FastAPI()

# Charger les variables d'environnement depuis .env
load_dotenv()

# Configuration de la base de données
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_NAME = os.getenv("DB_NAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DATABASE_URL = os.getenv("DATABASE_URL")

# Configuration (chargée depuis .env)
SECRET_KEY = "your_secret_key"
REFRESH_SECRET_KEY = "your_refresh_secret_key"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Connexion à la base de données
def get_db_connection():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=5432,
        cursor_factory=RealDictCursor
    )


# Modèles Pydantic
class SignUp(BaseModel):
    email: EmailStr
    password: str

class SignIn(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str

# Utilitaires pour JWT
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm="HS256")

# Hachage de mot de passe
def hash_password(password: str) -> str:
    return bcrypt.hash(password)

def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.verify(password, hashed_password)

# Routes
@app.post("/auth/signup")
def signup(user: SignUp):
    conn = get_db_connection()
    cur = conn.cursor()
    hashed_password = hash_password(user.password)

    try:
        cur.execute(
            """
            INSERT INTO users (email, password_hash)
            VALUES (%s, %s) RETURNING id
            """,
            (user.email, hashed_password)
        )
        user_id = cur.fetchone()["id"]
        conn.commit()
    except psycopg2.IntegrityError:
        conn.rollback()
        raise HTTPException(status_code=400, detail="User already exists")
    finally:
        cur.close()
        conn.close()

    return {"message": "Account created successfully"}

@app.post("/auth/signin", response_model=Token)
def signin(credentials: SignIn):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT id, password_hash FROM users WHERE email = %s
            """,
            (credentials.email,)
        )
        user = cur.fetchone()
        if not user or not verify_password(credentials.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Génération des tokens
        access_token = create_access_token({"sub": user["id"]})
        refresh_token = create_refresh_token({"sub": user["id"]})
        
        # Stockage du refresh token
        cur.execute(
            """
            INSERT INTO refresh_tokens (user_id, token, expires_at)
            VALUES (%s, %s, %s)
            """,
            (user["id"], refresh_token, datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()

    return {"access_token": access_token, "refresh_token": refresh_token}

@app.post("/auth/verify")
def verify_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.split(" ")[1]
    try:
        jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return {"valid": True}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/auth/refresh", response_model=Token)
def refresh_token(refresh_token: str):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Vérifier si le refresh token est valide
        payload = jwt.decode(refresh_token, REFRESH_SECRET_KEY, algorithms=["HS256"])
        user_id = payload["sub"]

        cur.execute(
            """
            SELECT token FROM refresh_tokens WHERE user_id = %s AND token = %s
            """,
            (user_id, refresh_token)
        )
        token_record = cur.fetchone()
        if not token_record:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        # Générer un nouveau access token
        access_token = create_access_token({"sub": user_id})
    finally:
        cur.close()
        conn.close()

    return {"access_token": access_token, "refresh_token": refresh_token}
