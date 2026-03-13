import sqlite3
import os

DB_PATH = os.getenv("DB_PATH", "demo_bot.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            current_lesson INTEGER DEFAULT 1,
            demo_done INTEGER DEFAULT 0,
            registered_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()


def get_user(user_id: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def create_user(user_id: int, username: str, full_name: str):
    conn = get_connection()
    conn.execute(
        "INSERT OR IGNORE INTO users (user_id, username, full_name) VALUES (?,?,?)",
        (user_id, username, full_name)
    )
    conn.commit()
    conn.close()


def advance_lesson(user_id: int):
    conn = get_connection()
    conn.execute("UPDATE users SET current_lesson = current_lesson + 1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()


def complete_demo(user_id: int):
    conn = get_connection()
    conn.execute("UPDATE users SET demo_done=1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()


def get_stats():
    conn = get_connection()
    total = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    done = conn.execute("SELECT COUNT(*) FROM users WHERE demo_done=1").fetchone()[0]
    conn.close()
    return {"total": total, "done": done}


def get_all_users():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM users ORDER BY registered_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_user(user_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM users WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()
