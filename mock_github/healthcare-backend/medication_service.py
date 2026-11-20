"""Medication history service."""
MEDICATIONS = {
    "P001": [{"name": "Metformin", "dose": "500 mg", "frequency": "twice daily"}],
    "P002": [{"name": "None recorded", "dose": None, "frequency": None}],
}


def get_medications(patient_id: str):
    return MEDICATIONS.get(patient_id, [])
