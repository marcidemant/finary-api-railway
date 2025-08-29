from fastapi import FastAPI, HTTPException
from datetime import datetime
import os
import requests
import json

app = FastAPI(title="Finary API for n8n", version="1.0.0")

# Session token global
auth_token = None
base_url = "https://api.finary.com"

@app.get("/")
def health_check():
    return {"status": "ok", "service": "finary-api", "version": "1.0.0"}

@app.post("/auth/signin")
def finary_signin():
    """Authentification directe API Finary"""
    global auth_token
    try:
        email = os.environ.get("FINARY_EMAIL")
        password = os.environ.get("FINARY_PASSWORD")
        
        if not email or not password:
            return {"success": False, "error": "Credentials manquants"}
        
        # Auth directe API Finary
        response = requests.post(f"{base_url}/v1/auth/signin", 
            json={"email": email, "password": password},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            auth_token = data.get("access_token")
            return {"success": True, "message": "Authentification réussie"}
        else:
            return {"success": False, "error": f"Auth failed: {response.status_code}"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/accounts") 
def get_accounts():
    """Récupération comptes via API"""
    global auth_token
    try:
        if not auth_token:
            return {"success": False, "error": "Non authentifié"}
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{base_url}/v1/accounts", headers=headers, timeout=30)
        
        if response.status_code == 200:
            accounts = response.json()
            return {"success": True, "count": len(accounts), "accounts": accounts}
        else:
            return {"success": False, "error": f"API error: {response.status_code}"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
