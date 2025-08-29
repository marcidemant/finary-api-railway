# api_finary.py - Service API Finary pour Railway
from fastapi import FastAPI, HTTPException
from datetime import datetime, timedelta
import subprocess
import json
import os

app = FastAPI(title="Finary API for n8n", version="1.0.0")

@app.get("/")
def health_check():
    return {
        "status": "ok", 
        "service": "finary-api",
        "version": "1.0.0"
    }

@app.post("/auth/signin")
def finary_signin():
    """Authentification Finary avec credentials env"""
    try:
        email = os.environ.get("FINARY_EMAIL")
        password = os.environ.get("FINARY_PASSWORD")
        
        if not email or not password:
            return {"success": False, "error": "Variables FINARY_EMAIL/PASSWORD manquantes"}
        
        # Créer le fichier jwt.json temporaire
        jwt_data = {"email": email, "password": password}
        with open("/app/jwt.json", "w") as f:
            json.dump(jwt_data, f)
        
        result = subprocess.run(
            ["python3", "-m", "finary_uapi", "signin"], 
            cwd="/app",
            capture_output=True, 
            text=True,
            timeout=30
        )
        
        return {
            "success": result.returncode == 0,
            "message": "Auth réussie" if result.returncode == 0 else "Échec auth"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/accounts")
def get_accounts():
    """Récupération des comptes bancaires"""
    try:
        result = subprocess.run([
            "python3", "-m", "finary_uapi", 
            "holdings_accounts", "checking"
        ], cwd="/app", capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            accounts = data.get("result", [])
            
            # Enrichissement pour n8n
            enriched_accounts = []
            for acc in accounts:
                enriched_accounts.append({
                    "id": acc.get("id"),
                    "name": acc.get("name"),
                    "bank": acc.get("bank_name", "Inconnu"),
                    "balance": acc.get("balance", 0),
                    "type": acc.get("account_type"),
                    "currency": acc.get("currency_code", "EUR"),
                    "sync_date": datetime.now().isoformat(),
                    "periode": datetime.now().strftime("%B %Y")
                })
            
            return {
                "success": True,
                "count": len(enriched_accounts),
                "accounts": enriched_accounts
            }
        else:
            return {"success": False, "error": result.stderr}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur récupération comptes: {str(e)}")

@app.get("/transactions")
def get_transactions(
    perpage: int = 500, 
    page: int = 1,
    account_id: str = None
):
    """Récupération des transactions"""
    try:
        cmd = [
            "python3", "-m", "finary_uapi",
            "checking_accounts", "transactions",
            f"--perpage={perpage}",
            f"--page={page}"
        ]
        
        if account_id:
            cmd.extend([f"--account={account_id}"])
        
        result = subprocess.run(
            cmd, 
            cwd="/app", 
            capture_output=True, 
            text=True, 
            timeout=120
        )
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            transactions = data.get("result", [])
            
            # Enrichissement pour comptabilité
            enriched_transactions = []
            for tx in transactions:
                enriched_transactions.append({
                    "id": tx.get("id"),
                    "date": tx.get("date"),
                    "description": tx.get("description") or tx.get("label", "Transaction"),
                    "amount": tx.get("amount", 0),
                    "currency": tx.get("currency_code", "EUR"),
                    "account_name": tx.get("account", {}).get("name"),
                    "bank_name": tx.get("account", {}).get("institution", {}).get("name"),
                    "category": tx.get("category", {}).get("name") if tx.get("category") else "Non classé",
                    "type": "CREDIT" if tx.get("amount", 0) > 0 else "DEBIT",
                    "amount_abs": abs(tx.get("amount", 0)),
                    "import_date": datetime.now().isoformat()
                })
            
            return {
                "success": True,
                "count": len(enriched_transactions),
                "page": page,
                "per_page": perpage,
                "transactions": enriched_transactions
            }
        else:
            return {"success": False, "error": result.stderr}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur récupération transactions: {str(e)}")

@app.get("/dashboard")
def get_dashboard():
    """Récupération dashboard global"""
    try:
        result = subprocess.run([
            "python3", "-m", "finary_uapi", "me"
        ], cwd="/app", capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return {"success": True, "dashboard": data.get("result", {})}
        else:
            return {"success": False, "error": result.stderr}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Point d'entrée pour Railway
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
