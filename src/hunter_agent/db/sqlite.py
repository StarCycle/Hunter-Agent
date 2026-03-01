from __future__ import annotations

import sqlite3
from pathlib import Path


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def run_sql_script(conn: sqlite3.Connection, script_path: Path) -> None:
    sql = script_path.read_text(encoding="utf-8")
    conn.executescript(sql)
    conn.commit()
