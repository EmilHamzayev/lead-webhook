"""Entry point: builds the app from environment variables.

Run with: uvicorn app.main:app
"""
import logging
import os

from app.api import create_app
from app.telegram import DryRunSender, Sender, TelegramSender

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def sender_from_env() -> Sender:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if token and chat_id:
        return TelegramSender(token, chat_id)
    logger.warning("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set: dry-run mode, messages are only logged")
    return DryRunSender()


app = create_app(os.getenv("DATABASE_PATH", "leads.db"), sender_from_env())
