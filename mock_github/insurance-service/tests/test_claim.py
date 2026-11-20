from claim_service import get_claim


def test_known_claim():
    assert get_claim("CLM-1001")["status"] == "approved"


def test_unknown_claim():
    assert get_claim("CLM-9999") is None
