import logging
from html import escape
from typing import Protocol

import httpx

from app.schemas import LeadIn

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org"
TIMEOUT_SECONDS = 5.0

CATEGORY_LABELS = {
    "booking": "Запис",
    "price": "Питання про ціну",
    "complaint": "Скарга",
    "other": "Інше",
}


def format_message(lead: LeadIn, category: str) -> str:
    # parse_mode=HTML, so every user-provided value must be escaped.
    label = CATEGORY_LABELS.get(category, category)
    return (
        "<b>Нова заявка</b>\n"
        f"Категорія: {escape(label)}\n"
        f"Ім'я: {escape(lead.name)}\n"
        f"Джерело: {escape(lead.source)}\n"
        f"ID: {escape(lead.external_id)}\n"
        "\n"
        f"{escape(lead.message)}"
    )


class TelegramError(Exception):
    """Any failure to deliver a message. Never contains the bot token."""


class Sender(Protocol):
    def send(self, text: str) -> None: ...


class TelegramSender:
    def __init__(self, token: str, chat_id: str, client: httpx.Client | None = None):
        self._url = f"{TELEGRAM_API}/bot{token}/sendMessage"
        self._chat_id = chat_id
        self._client = client or httpx.Client(timeout=TIMEOUT_SECONDS)

    def send(self, text: str) -> None:
        payload = {"chat_id": self._chat_id, "text": text, "parse_mode": "HTML"}
        try:
            response = self._client.post(self._url, json=payload)
        except httpx.HTTPError as exc:
            # httpx error messages may include the URL (and so the token): log the type only.
            raise TelegramError(f"network error: {type(exc).__name__}") from None

        try:
            data = response.json()
        except ValueError:
            data = {}

        if response.status_code != 200 or not data.get("ok"):
            description = data.get("description", "unknown error")
            raise TelegramError(f"HTTP {response.status_code}: {description}")


class DryRunSender:
    """Used when TELEGRAM_BOT_TOKEN is not set: logs instead of sending."""

    def send(self, text: str) -> None:
        logger.info("[dry-run] Telegram message:\n%s", text)
