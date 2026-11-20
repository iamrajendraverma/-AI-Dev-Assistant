"""Patient lookup service."""
PATIENTS = {
    "P001": {"patient_id": "P001", "name": "Alex Morgan"},
    "P002": {"patient_id": "P002", "name": "Sam Taylor"},
}


def get_patient(patient_id: str):
    return PATIENTS.get(patient_id)
