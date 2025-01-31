import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
import httpx

app = FastAPI()

# Load service URLs from environment variables
SERVICE_URLS = {
    "auth": os.getenv("AUTH_SERVICE"),
    "customers": os.getenv("CUSTOMER_SERVICE"),
    "betting": os.getenv("BETTING_SERVICE"),
    "notification": os.getenv("NOTIFICATION_SERVICE"),
    "odds": os.getenv("ODDS_SERVICE"),
    "payment": os.getenv("PAYMENT_SERVICE"),
    "card": os.getenv("CARD_SERVICE"),
    "bookmaker": os.getenv("BOOKMAKER_SERVICE"),
}

# Modèle pour récupérer les entrées utilisateur via Postman
class SignUpRequest(BaseModel):
    email: EmailStr
    password: str
    user_role: str
    firstname: str
    lastname: str
    birth_date: str  # Format: "YYYY-MM-DD"


@app.get("/")
def read_root():
    return {"message": "Gateway Service is Running"}

# Redirection dynamique des requêtes vers les services
@app.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_to_service(service: str, path: str, request: Request):
    if service not in SERVICE_URLS:
        raise HTTPException(status_code=404, detail=f"Service '{service}' not found")

    # Construire l'URL du service cible
    service_url = f"{SERVICE_URLS[service]}/{path}"

    try:
        # Transmettre la requête au service cible
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=request.method,
                url=service_url,
                headers=dict(request.headers),
                content=await request.body(),
            )
            return JSONResponse(status_code=response.status_code, content=response.json())
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Error connecting to service '{service}': {str(e)}")


# @app.post("/signup")
# async def signup(request: Request):
#     """
#     Gère l'inscription d'un utilisateur en appelant successivement Auth et Customer.
#     """
#     async with httpx.AsyncClient() as client:
#         # Étape 1: Appeler Auth Service pour créer un utilisateur
#         auth_url = f"{SERVICE_URLS['auth']}/auth/signup"
#         user_data = await request.json()

#         auth_response = await client.post(auth_url, json=user_data)
#         if auth_response.status_code != 200:
#             raise HTTPException(status_code=auth_response.status_code, detail=auth_response.json())

#         # Récupérer le user_id renvoyé par Auth
#         user_id = auth_response.json().get("user_id")

#         if not user_id:
#             raise HTTPException(status_code=500, detail="User ID missing from Auth service response")

#         # Étape 2: Ajouter l'utilisateur au service Customer
#         customer_url = f"{SERVICE_URLS['customers']}/customers/add"
#         customer_data = {
#             "username": user_data["email"],  # L'email est utilisé comme username
#             "user_id": user_id,
#             "firstname": user_data.get("firstname", ""),
#             "lastname": user_data.get("lastname", ""),
#             "birth_date": user_data.get("birth_date", "2000-01-01")  # Valeur par défaut
#         }

#         customer_response = await client.post(customer_url, json=customer_data)
#         if customer_response.status_code != 200:
#             raise HTTPException(status_code=customer_response.status_code, detail=customer_response.json())

#     return {"message": "User registered successfully"}

@app.post("/signup")
async def signup(user_data: SignUpRequest):
    """
    Gère l'inscription d'un utilisateur :
    - Récupère les entrées utilisateur (email, password, user_role, firstname, lastname, birth_date).
    - Appelle Auth Service pour créer l'utilisateur.
    - Récupère user_id de la réponse.
    - Appelle Customer Service pour enregistrer le client dans la base de données.
    """
    async with httpx.AsyncClient() as client:
        # Étape 1: Envoyer seulement email, password, user_role à Auth Service
        auth_url = f"{SERVICE_URLS['auth']}/auth/signup"
        auth_payload = {
            "email": user_data.email,
            "password": user_data.password,
            "user_role": user_data.user_role
        }

        auth_response = await client.post(auth_url, json=auth_payload)
        if auth_response.status_code != 200:
            raise HTTPException(status_code=auth_response.status_code, detail=auth_response.json())

        # Récupérer le user_id renvoyé par Auth
        auth_response_data = auth_response.json()
        user_id = auth_response_data.get("user_id")

        if not user_id:
            raise HTTPException(status_code=500, detail="User ID missing from Auth service response")

        # Étape 2: Envoyer firstname, lastname, birth_date au service Customer
        customer_url = f"{SERVICE_URLS['customers']}/customers/add"
        customer_payload = {
            "username": user_data.email,  # L'email est utilisé comme username
            "user_id": user_id,
            "firstname": user_data.firstname,
            "lastname": user_data.lastname,
            "birth_date": user_data.birth_date
        }

        customer_response = await client.post(customer_url, json=customer_payload)
        if customer_response.status_code != 200:
            raise HTTPException(status_code=customer_response.status_code, detail=customer_response.json())

    return {"message": "User registered successfully and added to customers"}

@app.post("/signin")
async def signin(request: Request):
    """
    Gère la connexion d'un utilisateur en appelant Auth pour obtenir un token.
    """
    async with httpx.AsyncClient() as client:
        auth_url = f"{SERVICE_URLS['auth']}/auth/signin"
        user_data = await request.json()

        auth_response = await client.post(auth_url, json=user_data)
        if auth_response.status_code != 200:
            raise HTTPException(status_code=auth_response.status_code, detail=auth_response.json())

    return auth_response.json()


@app.post("/verify-email")
async def verify_email(request: Request):
    """
    Vérifie l'email d'un utilisateur via le service Auth.
    """
    async with httpx.AsyncClient() as client:
        auth_url = f"{SERVICE_URLS['auth']}/auth/verify-email"
        verification_data = await request.json()

        # Vérifier que les données contiennent bien email et token
        required_fields = {"email", "token"}
        if not all(field in verification_data for field in required_fields):
            raise HTTPException(status_code=400, detail="Missing required fields (email, token)")

        # Transmettre la requête au service Auth
        auth_response = await client.post(auth_url, json=verification_data)
        if auth_response.status_code != 200:
            raise HTTPException(status_code=auth_response.status_code, detail=auth_response.json())

    return auth_response.json()
