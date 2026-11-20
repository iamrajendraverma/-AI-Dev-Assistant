"""Starter repository file: insurance-service."""
from fastapi import FastAPI, HTTPException
from claim_service import get_claim

app = FastAPI(title="Insurance Service")


@app.get("/claims/{claim_id}")
def claim_status(claim_id: str):
    claim = get_claim(claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail="Claim not found")
    return claim
