import sqlite3
import pytest
from datetime import date, timedelta

import db as db_module
from services.tasks import change_status, overdue, planned_for


@pytest.fixture
def conn(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", tmp_path / "test.db")
    c = db_module.connect(tmp_path / "test.db")
    yield c
    c.close()


def _add_task(conn, **kw):
    conn.execute(
        "INSERT INTO task (title, status, priority, due_date, planned_date) "
        "VALUES (?, ?, ?, ?, ?)",
        (
            kw.get("title", "t"),
            kw.get("status", "todo"),
            kw.get("priority", 2),
            kw.get("due_date"),
            kw.get("planned_date"),
        ),
    )
    conn.commit()
    return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def test_valid_transition(conn):
    tid = _add_task(conn)
    change_status(conn, tid, "in_progress")
    assert conn.execute("SELECT status FROM task WHERE id=?", (tid,)).fetchone()[0] == "in_progress"


def test_invalid_transition_raises(conn):
    tid = _add_task(conn, status="done")
    with pytest.raises(ValueError):
        change_status(conn, tid, "done")       # done → done запрещён


def test_done_sets_completed_at(conn):
    tid = _add_task(conn, status="in_progress")
    change_status(conn, tid, "done")
    row = conn.execute("SELECT completed_at FROM task WHERE id=?", (tid,)).fetchone()
    assert row[0] is not None


def test_overdue(conn):
    _add_task(conn, title="old", due_date=(date.today() - timedelta(days=1)).isoformat())
    _add_task(conn, title="done", due_date=(date.today() - timedelta(days=1)).isoformat(), status="done")
    _add_task(conn, title="future", due_date=(date.today() + timedelta(days=1)).isoformat())
    rows = overdue(conn)
    titles = [r["title"] for r in rows]
    assert titles == ["old"]


def test_planned_for(conn):
    today = date.today().isoformat()
    _add_task(conn, title="a", planned_date=today, priority=2)
    _add_task(conn, title="b", planned_date=today, priority=1)
    _add_task(conn, title="c", planned_date=today, status="done")
    rows = planned_for(conn, date.today())
    assert [r["title"] for r in rows] == ["b", "a"]     # по priority