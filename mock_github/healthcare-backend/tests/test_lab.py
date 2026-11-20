"""Starter tests; extend these for the ticket acceptance criteria."""
from lab_service import latest_hba1c


def test_latest_hba1c_for_p001():
    result = latest_hba1c("P001")
    assert result is not None
    assert result["value"] == 6.9


def test_unknown_patient_has_no_lab_result():
    assert latest_hba1c("P999") is None
