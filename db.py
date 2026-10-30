import sqlite3
import sys
import os
from pathlib import Path

# Определяем папку, где лежит сама программа (или бинарник)
if getattr(sys, 'frozen', False):
    # Если это скомпилированный PyInstaller бинарник
    APP_DIR = Path(sys.executable).parent
else:
    # Если это обычный запуск через python
    APP_DIR = Path(os.path.abspath(__file__)).parent

# Теперь база всегда будет лежать рядом с программой
DB_PATH = APP_DIR / "income.db"

SCHEMA_VERSION = 3

MIGRATIONS = {

    1: """
        CREATE TABLE client (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL UNIQUE,
            contact     TEXT,
            notes       TEXT DEFAULT '',
            created_at  TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE task (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id       INTEGER REFERENCES client(id) ON DELETE SET NULL,
            title           TEXT NOT NULL,
            description     TEXT DEFAULT '',
            status          TEXT NOT NULL DEFAULT 'todo'
                CHECK(status IN ('todo','in_progress','done','cancelled')),
            priority        INTEGER NOT NULL DEFAULT 2
                CHECK(priority IN (1,2,3)),
            due_date        TEXT,
            planned_date    TEXT,
            completed_at    TEXT,
            price_kopecks   INTEGER,
            hours_estimated REAL,
            hours_spent     REAL NOT NULL DEFAULT 0,
            created_at      TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX idx_task_status   ON task(status);
        CREATE INDEX idx_task_planned  ON task(planned_date);
        CREATE INDEX idx_task_due      ON task(due_date);

        CREATE TABLE income (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            date            TEXT NOT NULL,
            amount_kopecks  INTEGER NOT NULL,
            type            TEXT NOT NULL CHECK(type IN ('active','passive')),
            task_id         INTEGER REFERENCES task(id) ON DELETE SET NULL,
            description     TEXT DEFAULT '',
            created_at      TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX idx_income_date ON income(date);
        CREATE INDEX idx_income_task ON income(task_id);

        CREATE TABLE time_session (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id  INTEGER NOT NULL REFERENCES task(id) ON DELETE CASCADE,
            start    TEXT NOT NULL,
            end      TEXT,
            note     TEXT DEFAULT ''
        );
        CREATE INDEX idx_ts_task ON time_session(task_id);
        CREATE INDEX idx_ts_open ON time_session(end) WHERE end IS NULL;
    """,
    2: """
        CREATE TABLE personal_task (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            title         TEXT NOT NULL,
            description   TEXT DEFAULT '',
            status        TEXT NOT NULL DEFAULT 'todo' CHECK(status IN ('todo','in_progress','done')),
            planned_date  TEXT,
            created_at    TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE journal_log (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            date          TEXT NOT NULL,
            day_type      TEXT DEFAULT 'work', -- 'work', 'study', 'rest'
            note          TEXT DEFAULT ''
        );
    """,
    3: """
        CREATE TABLE settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );
    """
}

def connect(path: Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    _migrate(conn)
    return conn

def _migrate(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA user_version")
    current = conn.execute("PRAGMA user_version").fetchone()[0]
    for version in sorted(MIGRATIONS):
        if version > current:
            conn.executescript(MIGRATIONS[version])
            conn.execute(f"PRAGMA user_version = {version}")
    conn.commit()