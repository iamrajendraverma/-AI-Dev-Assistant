"""Insurance claim service."""
CLAIMS = {
    "CLM-1001": {"claim_id": "CLM-1001", "status": "approved", "amount": 1250.00},
    "CLM-1002": {"claim_id": "CLM-1002", "status": "under_review", "amount": 840.00},
}


def get_claim(claim_id: str):
    return CLAIMS.get(claim_id)
