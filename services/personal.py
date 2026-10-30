from datetime import date

def get_journal(conn, day: date):
    """Получить или создать запись дневника на день."""
    row = conn.execute("SELECT * FROM journal_log WHERE date = ?", (day.isoformat(),)).fetchone()
    if not row:
        conn.execute("INSERT INTO journal_log (date, day_type, note) VALUES (?, 'work', '')", (day.isoformat(),))
        conn.commit()
        row = conn.execute("SELECT * FROM journal_log WHERE date = ?", (day.isoformat(),)).fetchone()
    return dict(row) if row else None

def save_journal(conn, day: date, day_type: str, note: str):
    conn.execute(
        "UPDATE journal_log SET day_type = ?, note = ? WHERE date = ?",
        (day_type, note, day.isoformat())
    )
    conn.commit()

def get_personal_tasks(conn, day: date):
    rows = conn.execute(
        "SELECT * FROM personal_task WHERE planned_date = ? ORDER BY status, id",
        (day.isoformat(),)
    ).fetchall()
    return [dict(r) for r in rows]

def add_personal_task(conn, title, desc, day: date):
    conn.execute(
        "INSERT INTO personal_task (title, description, planned_date) VALUES (?, ?, ?)",
        (title, desc, day.isoformat())
    )
    conn.commit()

def update_personal_task(conn, task_id: int, title: str, desc: str):
    conn.execute(
        "UPDATE personal_task SET title = ?, description = ? WHERE id = ?",
        (title, desc, task_id)
    )
    conn.commit()

def delete_personal_task(conn, task_id: int):
    conn.execute("DELETE FROM personal_task WHERE id = ?", (task_id,))
    conn.commit()