import httpx
import pytest

from app.schemas import LeadIn
from app.telegram import TelegramError, TelegramSender, format_message

TOKEN = "123:SECRET"


def make_sender(handler) -> TelegramSender:
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return TelegramSender(TOKEN, "42", client=client)


def make_lead(**overrides) -> LeadIn:
    data = {
        "external_id": "lead-1001",
        "name": "Anna",
        "message": "Хочу записатися на процедуру наступного тижня",
        "source": "instagram",
    }
    return LeadIn(**{**data, **overrides})


def test_message_contains_lead_fields():
    text = format_message(make_lead(), "booking")
    assert "Категорія: Запис" in text
    assert "Ім'я: Anna" in text
    assert "Джерело: instagram" in text
    assert "ID: lead-1001" in text
    assert "Хочу записатися" in text


def test_user_input_is_html_escaped():
    text = format_message(make_lead(name="<b>Hacker</b>"), "other")
    assert "<b>Hacker</b>" not in text
    assert "&lt;b&gt;Hacker&lt;/b&gt;" in text


def test_send_posts_to_telegram_api():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["json"] = request.read().decode()
        return httpx.Response(200, json={"ok": True, "result": {}})

    make_sender(handler).send("hello")

    assert captured["url"] == f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    assert '"chat_id":"42"' in captured["json"].replace(" ", "")


def test_send_raises_on_telegram_error_response():
    def handler(request):
        return httpx.Response(400, json={"ok": False, "description": "Bad Request: chat not found"})

    with pytest.raises(TelegramError, match="chat not found"):
        make_sender(handler).send("hello")


def test_send_raises_on_network_error_without_leaking_token():
    def handler(request):
        raise httpx.ConnectTimeout("timed out", request=request)

    with pytest.raises(TelegramError) as exc_info:
        make_sender(handler).send("hello")

    assert "network error" in str(exc_info.value)
    assert "SECRET" not in str(exc_info.value)
