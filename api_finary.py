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
    """Auth avec credentials directs"""
    try:
        email = os.environ.get("FINARY_EMAIL")
        password = os.environ.get("FINARY_PASSWORD")
        
        if not email or not password:
            return {"success": False, "error": "Credentials manquants"}
        
        # Créer fichier temporaire pour auth
        jwt_data = {"email": email, "password": password}
        with open("/tmp/jwt.json", "w") as f:
            json.dump(jwt_data, f)
            
        # Pointer finary vers ce fichier
        os.environ["FINARY_JWT_FILE"] = "/tmp/jwt.json"
        
        result = subprocess.run([
            "python3", "-m", "finary_uapi", "me"
        ], cwd="/app", capture_output=True, text=True, timeout=30)
        
        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout[:200],
            "stderr": result.stderr[:200]
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

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
