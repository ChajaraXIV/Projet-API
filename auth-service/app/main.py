from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel, EmailStr
from passlib.hash import bcrypt
from datetime import datetime, timedelta
import jwt
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os
import asyncio

# Initialisation de FastAPI
app = FastAPI()

# Charger les variables d'environnement depuis .env
load_dotenv()

# Configuration de la base de données
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_NAME = os.getenv("DB_NAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Configuration JWT
SECRET_KEY = os.getenv("SECRET_KEY")
REFRESH_SECRET_KEY = os.getenv("REFRESH_SECRET_KEY")
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
    user_role : str

class SignIn(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class LogoutRequest(BaseModel):
    email: EmailStr
    password: str
    token: str

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

#création du compte admin 
def create_admin_account():
    # Obtenez les variables d'environnement pour l'admin
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASSWORD")

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Vérifier si un compte admin existe déjà
        cur.execute(
            """
            SELECT id FROM users WHERE email = %s
            """,
            (admin_email,)
        )
        if cur.fetchone():
            print("Admin account already exists.")
            return

        # Hacher le mot de passe
        hashed_password = hash_password(admin_password)

        # Créer un compte admin
        cur.execute(
            """
            INSERT INTO users (email, password_hash, user_role)
            VALUES (%s, %s, %s)
            """,
            (admin_email, hashed_password, "admin")
        )
        conn.commit()
        print("Admin account created successfully.")
    except Exception as e:
        print(f"Error creating admin account: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

#get current user
def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    if "sub" not in payload:
        raise HTTPException(status_code=400, detail="Invalid token payload: missing 'sub'")
    if "role" not in payload:
        raise HTTPException(status_code=400, detail="Invalid token payload: missing 'role'")
    
    return payload

#check les tokens 
async def invalidate_expired_tokens():
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            UPDATE tokens SET valid = FALSE WHERE expires_at < NOW()
            """
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()

async def check_and_refresh_connected_users():
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Obtenir tous les utilisateurs connectés
        cur.execute(
            """
            SELECT id, email FROM users WHERE connected = TRUE
            """
        )
        connected_users = cur.fetchall()

        for user in connected_users:
            user_id = user["id"]

            # Vérifier si l'utilisateur a un access token valide
            cur.execute(
                """
                SELECT token FROM tokens
                WHERE user_id = %s AND token_type = 'access' AND valid = TRUE
                """,
                (user_id,)
            )
            access_token = cur.fetchone()

            if not access_token:
                # Si pas d'access token valide, vérifier le refresh token
                cur.execute(
                    """
                    SELECT token FROM tokens
                    WHERE user_id = %s AND token_type = 'refresh' AND valid = TRUE
                    """,
                    (user_id,)
                )
                refresh_token_record = cur.fetchone()

                if refresh_token_record:
                    refresh_token = refresh_token_record["token"]

                    try:
                        # Décoder le refresh token pour vérifier sa validité
                        payload = jwt.decode(refresh_token, REFRESH_SECRET_KEY, algorithms=["HS256"])
                        user_role = payload["role"]

                        # Générer un nouveau access token
                        new_access_token = create_access_token({"sub": str(user_id), "role": user_role})

                        # Stocker le nouveau access token
                        cur.execute(
                            """
                            INSERT INTO tokens (user_id, token, token_type, expires_at, valid)
                            VALUES (%s, %s, %s, %s, TRUE)
                            """,
                            (
                                user_id,
                                new_access_token,
                                "access",
                                datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
                            )
                        )
                        conn.commit()
                        print(f"Access token refreshed for user {user['email']}")

                    except jwt.ExpiredSignatureError:
                        print(f"Refresh token expired for user {user['email']}")
                    except jwt.InvalidTokenError:
                        print(f"Invalid refresh token for user {user['email']}")
                else:
                    print(f"No valid refresh token found for user {user['email']}")
                    cur.execute(
                        """
                        UPDATE users SET connected = FALSE WHERE user_id = %s
                        """,
                        (user_id,)
                    )
                    conn.commit()
    finally:
        cur.close()
        conn.close()

#appeler la fonction d'admin et check des tokens 
@app.on_event("startup")
async def startup_event():
    create_admin_account()
    asyncio.create_task(periodic_invalidation())
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            UPDATE users SET connected = FALSE
            """
        )
        cur.execute(
            """
            UPDATE tokens SET valid = FALSE WHERE token_type = 'access'
            """
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()

async def periodic_invalidation():
    while True:
        await invalidate_expired_tokens()
        await check_and_refresh_connected_users()
        await asyncio.sleep(10)


# Routes
@app.post("/auth/signup")
def signup(user: SignUp):
    conn = get_db_connection()
    cur = conn.cursor()
    hashed_password = hash_password(user.password)

    try:
        cur.execute(
            """
            INSERT INTO users (email, password_hash,user_role)
            VALUES (%s, %s, %s) RETURNING id
            """,
            (user.email, hashed_password, user.user_role)
        )
        user_id = cur.fetchone()["id"]
        conn.commit()
    except psycopg2.IntegrityError as e:
        conn.rollback()
        if "unique constraint" in str(e):
            raise HTTPException(status_code=400, detail="User already exists")
        else:
            raise HTTPException(status_code=500, detail="An unexpected error occurred")
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
            SELECT id, password_hash, user_role, connected FROM users WHERE email = %s
            """,
            (credentials.email,)
        )
        user = cur.fetchone()
        if not user or not verify_password(credentials.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Vérifier si l'utilisateur est déjà connecté
        if user["connected"]:
            raise HTTPException(status_code=400, detail="User already signed in")
        
        # Vérifier les sessions d'autres utilisateurs
        cur.execute(
            """
            SELECT token FROM tokens WHERE user_id <> %s AND token_type = 'access' AND valid = TRUE
            """,
            (user["id"],)
        )
        other_access_tokens = cur.fetchall()
        if other_access_tokens:
            raise HTTPException(status_code=400, detail="Please logout from the current account first")
        
        # Génération des tokens
        cur.execute(
            """
            SELECT token FROM tokens WHERE user_id = %s AND token_type = 'refresh' AND valid = TRUE
            """,
            (user["id"],)
        )
        refresh_token_record = cur.fetchone()
        if refresh_token_record:
            refresh_token = refresh_token_record["token"]
        else:
            refresh_token = create_refresh_token({"sub": str(user["id"]), "role": user["user_role"]})
            # Stockage du refresh token
            cur.execute(
                """
                INSERT INTO tokens (user_id, token, token_type, expires_at, valid)
                VALUES (%s, %s, %s, %s, TRUE)
                """,
                (user["id"], refresh_token, "refresh", datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
            )
        
        
        access_token = create_access_token({"sub": str(user["id"]), "role": user["user_role"]})
        cur.execute(
            """
            INSERT INTO tokens (user_id, token, token_type, expires_at, valid)
            VALUES (%s, %s, %s, %s, TRUE)
            """,
            (user["id"], access_token, "access", datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        )

        # Mettre à jour l'état "connected" et stocker les tokens
        cur.execute(
            """
            UPDATE users SET connected = TRUE WHERE id = %s
            """,
            (user["id"],)
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()

    return {"access_token": access_token, "refresh_token": refresh_token}

@app.post("/auth/verify")
def verify_token(current_user: dict = Depends(get_current_user)):
    return {
        "user_id": current_user.get("sub"),
        "role": current_user.get("role"),
        "message": "Token is valid"
    }

@app.post("/auth/logout")
def logout(request: LogoutRequest):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Vérifier l'utilisateur avec email et mot de passe
        cur.execute(
            """
            SELECT id, password_hash FROM users WHERE email = %s
            """,
            (request.email,)
        )
        user = cur.fetchone()
        if not user or not verify_password(request.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Vérifier si le token appartient bien à cet utilisateur
        cur.execute(
            """
            SELECT token FROM tokens WHERE user_id = %s AND token = %s AND token_type = 'access' AND valid = TRUE
            """,
            (user["id"], request.token)
        )
        token_record = cur.fetchone()
        if not token_record:
            raise HTTPException(status_code=401, detail="Invalid or already logged-out token")

        # Rendre les tokens de cet utilisateur invalides et mettre connected à FALSE
        cur.execute(
            """
            UPDATE tokens SET valid = FALSE WHERE user_id = %s AND token_type = 'access'
            """,
            (user["id"],)
        )
        cur.execute(
            """
            UPDATE users SET connected = FALSE WHERE id = %s
            """,
            (user["id"],)
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()

    return {"message": "Successfully logged out"}


@app.post("/auth/refresh", response_model=Token)
def refresh_token(request: RefreshTokenRequest):
    refresh_token = request.refresh_token
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Vérifier si le refresh token est valide
        payload = jwt.decode(refresh_token, REFRESH_SECRET_KEY, algorithms=["HS256"])
        
        # Vérifie que les champs nécessaires sont présents
        if "sub" not in payload:
            raise HTTPException(status_code=400, detail="Invalid token payload: missing 'sub'")
        if "role" not in payload:
            raise HTTPException(status_code=400, detail="Invalid token payload: missing 'role'")
        
        user_id = payload["sub"]
        user_role = payload["role"]

        cur.execute(
            """
            SELECT token FROM tokens WHERE user_id = %s AND token = %s AND token_type = %s
            """,
            (user_id, refresh_token, "refresh")
        )

        token_record = cur.fetchone()
        if not token_record:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        # Générer un nouveau access token
        access_token = create_access_token({"sub": str(user_id), "role": user_role})
    finally:
        cur.close()
        conn.close()

    return {"access_token": access_token, "refresh_token": refresh_token}

@app.delete("/auth/delete/{user_id}")
def delete_user(user_id: int, current_user: dict = Depends(get_current_user)):
    # Vérifier les permissions
    if current_user["role"] == "admin" and current_user["sub"] == str(user_id):
        raise HTTPException(status_code=403, detail="Cannot delete admin account")
    if current_user["role"] != "admin" and current_user["sub"] != str(user_id):
        raise HTTPException(status_code=403, detail="Not authorized to delete this user")
    
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Vérifier si l'utilisateur existe
        cur.execute(
            """
            SELECT id FROM users WHERE id = %s
            """,
            (user_id,)
        )
        user = cur.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Supprimer tous les tokens associés
        cur.execute(
            """
            DELETE FROM tokens WHERE user_id = %s
            """,
            (user_id,)
        )

        # Supprimer l'utilisateur
        cur.execute(
            """
            DELETE FROM users WHERE id = %s
            """,
            (user_id,)
        )

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    finally:
        cur.close()
        conn.close()

    return {"message": f"User with ID {user_id} has been deleted successfully"}
