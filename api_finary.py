from fastapi import FastAPI, HTTPException
from datetime import datetime
import os
import json

app = FastAPI(title="Finary API for n8n", version="1.0.0")

# Session Finary globale
finary_session = None

@app.get("/")
def health_check():
    return {"status": "ok", "service": "finary-api", "version": "1.0.0"}

@app.post("/auth/signin")
def finary_signin():
    """Authentification directe avec finary_uapi"""
    global finary_session
    try:
        from finary_uapi.auth import FinaryAuth
        
        email = os.environ.get("FINARY_EMAIL")
        password = os.environ.get("FINARY_PASSWORD")
        
        if not email or not password:
            raise HTTPException(status_code=400, detail="Variables FINARY_EMAIL/PASSWORD manquantes")
        
        auth = FinaryAuth()
        finary_session = auth.login(email, password)
        
        return {"success": True, "message": "Authentification réussie"}
        
    except Exception as e:
        return {"success": False, "error": f"Erreur auth: {str(e)}"}

@app.get("/accounts")
def get_accounts():
    """Récupération des comptes"""
    global finary_session
    try:
        if not finary_session:
            raise HTTPException(status_code=401, detail="Non authentifié - appelez /auth/signin d'abord")
        
        from finary_uapi.checking_accounts import CheckingAccounts
        checking = CheckingAccounts(finary_session)
        accounts = checking.get_accounts()
        
        return {"success": True, "count": len(accounts), "accounts": accounts}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
