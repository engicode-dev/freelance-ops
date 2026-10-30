from datetime import datetime

def active_session(conn):
    row = conn.execute(
        "SELECT * FROM time_session WHERE end IS NULL ORDER BY id DESC LIMIT 1"
    ).fetchone()
    return dict(row) if row else None

def start(conn, task_id: int) -> int:
    if active_session(conn):
        raise RuntimeError("уже идёт таймер — сначала stop")
    now = datetime.now().isoformat()
    cur = conn.execute(
        "INSERT INTO time_session (task_id, start) VALUES (?, ?)",
        (task_id, now),
    )
    conn.execute(
        "UPDATE task SET status = 'in_progress' WHERE id = ? AND status = 'todo'",
        (task_id,),
    )
    conn.commit()
    return cur.lastrowid

def stop(conn) -> float:
    s = active_session(conn)
    if not s:
        raise RuntimeError("нет активного таймера")
    now = datetime.now()
    start_dt = datetime.fromisoformat(s["start"])
    hours = (now - start_dt).total_seconds() / 3600.0

    conn.execute("UPDATE time_session SET end = ? WHERE id = ?",
                 (now.isoformat(), s["id"]))
    conn.execute("UPDATE task SET hours_spent = hours_spent + ? WHERE id = ?",
                 (hours, s["task_id"]))
    conn.commit()
    return hours