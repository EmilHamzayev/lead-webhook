import pytest
from fastapi.testclient import TestClient

from app.api import create_app
from app.telegram import TelegramError

PAYLOAD = {
    "external_id": "lead-1001",
    "name": "Anna",
    "message": "Хочу записатися на процедуру наступного тижня",
    "source": "instagram",
}


class FakeSender:
    def __init__(self, fail: bool = False):
        self.fail = fail
        self.sent: list[str] = []

    def send(self, text: str) -> None:
        if self.fail:
            raise TelegramError("HTTP 400: chat not found")
        self.sent.append(text)


@pytest.fixture
def sender():
    return FakeSender()


@pytest.fixture
def client(tmp_path, sender):
    app = create_app(str(tmp_path / "test.db"), sender)
    return TestClient(app)


def test_new_lead_is_categorized_sent_and_saved(client, sender):
    response = client.post("/webhook/lead", json=PAYLOAD)

    assert response.status_code == 201
    assert response.json() == {
        "external_id": "lead-1001",
        "category": "booking",
        "status": "sent",
        "duplicate": False,
    }
    assert len(sender.sent) == 1
    assert "Anna" in sender.sent[0]

    saved = client.get("/leads/lead-1001").json()
    assert saved["status"] == "sent"
    assert saved["category"] == "booking"


def test_duplicate_lead_is_not_processed_again(client, sender):
    client.post("/webhook/lead", json=PAYLOAD)
    response = client.post("/webhook/lead", json=PAYLOAD)

    assert response.status_code == 200
    assert response.json()["duplicate"] is True
    assert len(sender.sent) == 1  # Telegram was called only once


def test_telegram_failure_is_saved_as_failed(tmp_path):
    client = TestClient(create_app(str(tmp_path / "test.db"), FakeSender(fail=True)))

    response = client.post("/webhook/lead", json=PAYLOAD)

    assert response.status_code == 201
    assert response.json()["status"] == "failed"

    saved = client.get("/leads/lead-1001").json()
    assert saved["status"] == "failed"
    assert "chat not found" in saved["error"]


def test_invalid_payload_returns_422_and_is_not_saved(client, sender):
    response = client.post("/webhook/lead", json={**PAYLOAD, "name": ""})

    assert response.status_code == 422
    assert sender.sent == []
    assert client.get("/leads/lead-1001").status_code == 404
