import pytest

from app import db


@pytest.fixture
def conn():
    connection = db.connect(":memory:")
    db.init_db(connection)
    yield connection
    connection.close()


def insert(conn, external_id="lead-1001"):
    return db.insert_lead(
        conn,
        external_id=external_id,
        name="Anna",
        message="Хочу записатися",
        source="instagram",
        category="booking",
    )


def test_insert_saves_lead_with_received_status(conn):
    lead_id = insert(conn)
    assert lead_id is not None

    row = db.get_lead(conn, "lead-1001")
    assert row["name"] == "Anna"
    assert row["category"] == "booking"
    assert row["status"] == db.STATUS_RECEIVED
    assert row["error"] is None


def test_duplicate_external_id_is_not_inserted(conn):
    assert insert(conn) is not None
    assert insert(conn) is None

    count = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
    assert count == 1


def test_different_external_ids_are_both_inserted(conn):
    assert insert(conn, "lead-1") is not None
    assert insert(conn, "lead-2") is not None


def test_set_status_failed_stores_error(conn):
    lead_id = insert(conn)
    db.set_status(conn, lead_id, db.STATUS_FAILED, "timeout")

    row = db.get_lead(conn, "lead-1001")
    assert row["status"] == db.STATUS_FAILED
    assert row["error"] == "timeout"
