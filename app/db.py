import sqlite3

STATUS_RECEIVED = "received"
STATUS_SENT = "sent"
STATUS_FAILED = "failed"

SCHEMA = """
CREATE TABLE IF NOT EXISTS leads (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    external_id TEXT NOT NULL UNIQUE,
    name        TEXT NOT NULL,
    message     TEXT NOT NULL,
    source      TEXT NOT NULL,
    category    TEXT NOT NULL,
    status      TEXT NOT NULL,
    error       TEXT,
    created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""


def connect(path: str) -> sqlite3.Connection:
    # check_same_thread=False: FastAPI may run sync endpoints in a thread pool.
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    with conn:
        conn.execute(SCHEMA)


def insert_lead(conn: sqlite3.Connection, *, external_id: str, name: str,
                message: str, source: str, category: str) -> int | None:
    """Insert a new lead. Returns its id, or None if external_id already exists.

    The UNIQUE constraint makes the duplicate check atomic, so two concurrent
    requests with the same external_id cannot both be processed.
    """
    with conn:
        cur = conn.execute(
            """
            INSERT INTO leads (external_id, name, message, source, category, status)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(external_id) DO NOTHING
            """,
            (external_id, name, message, source, category, STATUS_RECEIVED),
        )
    return cur.lastrowid if cur.rowcount == 1 else None


def set_status(conn: sqlite3.Connection, lead_id: int, status: str,
               error: str | None = None) -> None:
    with conn:
        conn.execute(
            "UPDATE leads SET status = ?, error = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, error, lead_id),
        )


def get_lead(conn: sqlite3.Connection, external_id: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM leads WHERE external_id = ?", (external_id,)
    ).fetchone()
