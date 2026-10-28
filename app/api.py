import logging
import sqlite3
from collections.abc import Iterator

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse

from app import db
from app.categorizer import categorize
from app.schemas import LeadIn
from app.telegram import Sender, TelegramError, format_message

logger = logging.getLogger(__name__)


def create_app(db_path: str, sender: Sender) -> FastAPI:
    """App factory: tests pass a temp database and a fake sender."""
    app = FastAPI(title="Lead webhook")

    conn = db.connect(db_path)
    db.init_db(conn)
    conn.close()

    # One connection per request: sync endpoints run in a thread pool,
    # and sharing one SQLite connection across threads is unsafe.
    def get_conn() -> Iterator[sqlite3.Connection]:
        conn = db.connect(db_path)
        try:
            yield conn
        finally:
            conn.close()

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/webhook/lead", status_code=201)
    def receive_lead(lead: LeadIn, conn: sqlite3.Connection = Depends(get_conn)):
        category = categorize(lead.message)
        lead_id = db.insert_lead(conn, **lead.model_dump(), category=category)

        if lead_id is None:
            # Already processed: 200 so the caller does not retry, and no second Telegram message.
            existing = db.get_lead(conn, lead.external_id)
            return JSONResponse(status_code=200, content={
                "external_id": lead.external_id,
                "category": existing["category"],
                "status": existing["status"],
                "duplicate": True,
            })

        try:
            sender.send(format_message(lead, category))
        except TelegramError as exc:
            # The lead is already saved, so we still answer 201 and keep the error for a later retry.
            logger.error("Telegram delivery failed for %s: %s", lead.external_id, exc)
            db.set_status(conn, lead_id, db.STATUS_FAILED, str(exc))
            lead_status = db.STATUS_FAILED
        else:
            db.set_status(conn, lead_id, db.STATUS_SENT)
            lead_status = db.STATUS_SENT

        return {
            "external_id": lead.external_id,
            "category": category,
            "status": lead_status,
            "duplicate": False,
        }

    @app.get("/leads/{external_id}")
    def get_lead(external_id: str, conn: sqlite3.Connection = Depends(get_conn)):
        row = db.get_lead(conn, external_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Lead not found")
        return dict(row)

    return app
