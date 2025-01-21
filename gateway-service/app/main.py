from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
import httpx

app = FastAPI()

# Dictionnaire des services avec leurs URL internes Docker
services = {
    "auth": "http://auth-service:80",  # URL interne du service auth-service
    "betting": "http://betting-service:80",  # Ajoutez d'autres services ici si nécessaire
    "odds": "http://auth-service:80",  # URL interne du service auth-service
    "betting": "http://betting-service:80",  # Ajoutez d'autres services ici si nécessaire
}

# Page d'accueil pour navigation vers les services
@app.get("/", response_class=HTMLResponse)
def read_root():
    html_content = """
    <html>
        <head>
            <title>Gateway Menu</title>
        </head>
        <body>
            <h1>Gateway Menu</h1>
            <ul>
                <li><a href="/auth">Auth Service Health Check</a></li>
                <li><a href="/betting">Access Betting Service</a></li>
                <!-- Ajoutez d'autres services ici -->
            </ul>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# Redirection dynamique des requêtes vers les services
@app.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_to_service(service: str, path: str, request: Request):
    if service not in services:
        raise HTTPException(status_code=404, detail=f"Service '{service}' not found")

    # Construire l'URL du service cible
    service_url = f"{services[service]}/{path}"

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