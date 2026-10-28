import pytest
from pydantic import ValidationError

from app.schemas import LeadIn

VALID = {
    "external_id": "lead-1001",
    "name": "Anna",
    "message": "Хочу записатися на процедуру наступного тижня",
    "source": "instagram",
}


def test_valid_payload_is_accepted():
    lead = LeadIn(**VALID)
    assert lead.external_id == "lead-1001"
    assert lead.source == "instagram"


def test_whitespace_is_trimmed():
    lead = LeadIn(**{**VALID, "name": "  Anna  "})
    assert lead.name == "Anna"


@pytest.mark.parametrize("field", ["external_id", "name", "message", "source"])
def test_missing_field_is_rejected(field):
    data = {k: v for k, v in VALID.items() if k != field}
    with pytest.raises(ValidationError):
        LeadIn(**data)


@pytest.mark.parametrize("field", ["external_id", "name", "message", "source"])
def test_blank_field_is_rejected(field):
    with pytest.raises(ValidationError):
        LeadIn(**{**VALID, field: "   "})
