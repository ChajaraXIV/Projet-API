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
}

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
