"""Laboratory result service — starter implementation."""
LAB_RESULTS = [
    {"patient_id": "P001", "test_name": "HbA1c", "value": 7.2, "unit": "%", "date": "2026-10-12"},
    {"patient_id": "P001", "test_name": "HbA1c", "value": 6.9, "unit": "%", "date": "2026-11-02"},
    {"patient_id": "P001", "test_name": "Fasting glucose", "value": 112, "unit": "mg/dL", "date": "2026-11-02"},
    {"patient_id": "P002", "test_name": "HbA1c", "value": 5.8, "unit": "%", "date": "2026-09-20"},
]


def latest_hba1c(patient_id: str):
    """Return latest HbA1c row for a patient; intentionally minimal."""
    matches = [
        row for row in LAB_RESULTS
        if row["patient_id"] == patient_id and row["test_name"] == "HbA1c"
    ]
    return sorted(matches, key=lambda row: row["date"], reverse=True)[0] if matches else None
