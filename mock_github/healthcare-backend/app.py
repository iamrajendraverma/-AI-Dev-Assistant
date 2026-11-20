"""Starter repository file: healthcare-backend."""
from fastapi import FastAPI, HTTPException
from lab_service import latest_hba1c

app = FastAPI(title="Healthcare Backend")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/patients/{patient_id}/labs/hba1c")
def get_hba1c(patient_id: str):
    # Existing endpoint is intentionally incomplete for PROJ-101.
    result = latest_hba1c(patient_id)
    if result is None:
        raise HTTPException(status_code=404, detail="HbA1c result not found")
    return result
