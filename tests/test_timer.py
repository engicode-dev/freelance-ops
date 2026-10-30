import sqlite3
import pytest
from datetime import datetime, timedelta

import db as db_module
from services import timer


@pytest.fixture
def conn(tmp_path):
    c = db_module.connect(tmp_path / "test.db")
    c.execute("INSERT INTO task (title) VALUES ('t')")
    c.commit()
    yield c
    c.close()


def _task_id(conn):
    return conn.execute("SELECT id FROM task").fetchone()[0]


def test_start_creates_open_session(conn):
    tid = _task_id(conn)
    timer.start(conn, tid)
    s = timer.active_session(conn)
    assert s is not None
    assert s["end"] is None


def test_double_start_raises(conn):
    tid = _task_id(conn)
    timer.start(conn, tid)
    with pytest.raises(RuntimeError):
        timer.start(conn, tid)


def test_stop_without_start_raises(conn):
    with pytest.raises(RuntimeError):
        timer.stop(conn)


def test_stop_updates_hours_spent(conn):
    tid = _task_id(conn)
    timer.start(conn, tid)
    # искусственно «сдвигаем» старт на час назад
    conn.execute(
        "UPDATE time_session SET start = ? WHERE end IS NULL",
        ((datetime.now() - timedelta(hours=1)).isoformat(),),
    )
    conn.commit()
    hours = timer.stop(conn)
    assert 0.99 < hours < 1.01
    row = conn.execute("SELECT hours_spent FROM task WHERE id=?", (tid,)).fetchone()
    assert 0.99 < row[0] < 1.01


def test_start_sets_in_progress(conn):
    tid = _task_id(conn)
    timer.start(conn, tid)
    status = conn.execute("SELECT status FROM task WHERE id=?", (tid,)).fetchone()[0]
    assert status == "in_progress"