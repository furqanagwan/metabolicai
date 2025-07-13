import sqlite3
from pathlib import Path
from typing import Optional
from app.schemas import UserProfile, Entry

DB_PATH = Path("data/entries.db")


def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            height_cm REAL,
            body_fat_pct REAL,
            current_weight REAL
        )
    """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS entries (
            user_id TEXT NOT NULL,
            date TEXT NOT NULL,
            weight REAL,
            calories INTEGER,
            PRIMARY KEY (user_id, date)
        )
    """
    )
    conn.commit()
    conn.close()


def upsert_user(profile: UserProfile):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO users (user_id, age, gender, height_cm, body_fat_pct, current_weight)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
          age=excluded.age,
          gender=excluded.gender,
          height_cm=excluded.height_cm,
          body_fat_pct=excluded.body_fat_pct,
          current_weight=excluded.current_weight
    """,
        (
            profile.user_id,
            profile.age,
            profile.gender,
            profile.height_cm,
            profile.body_fat_pct,
            profile.current_weight,
        ),
    )
    conn.commit()
    conn.close()


def get_user(user_id: str) -> Optional[UserProfile]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT user_id, age, gender, height_cm, body_fat_pct, current_weight FROM users WHERE user_id = ?",
        (user_id,),
    )
    row = cur.fetchone()
    conn.close()
    if row:
        return UserProfile(
            user_id=row[0],
            age=row[1],
            gender=row[2],
            height_cm=row[3],
            body_fat_pct=row[4],
            current_weight=row[5],
        )
    return None


def upsert_entry(user_id: str, entry: Entry):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO entries (user_id, date, weight, calories)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id, date) DO UPDATE SET
            weight=COALESCE(excluded.weight, weight),
            calories=COALESCE(excluded.calories, calories)
    """,
        (user_id, entry.date.isoformat(), entry.weight, entry.calories),
    )
    conn.commit()
    conn.close()


def get_entries(user_id: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT date, weight, calories FROM entries
        WHERE user_id = ?
        ORDER BY date
    """,
        (user_id,),
    )
    result = [
        {"date": row[0], "weight": row[1], "calories": row[2]} for row in cur.fetchall()
    ]
    conn.close()
    return result


def get_entries_df(user_id: str):
    import pandas as pd

    rows = get_entries(user_id)
    if not rows:
        return None
    return pd.DataFrame(rows)


def get_user_profile(user_id: str) -> Optional[dict]:
    user = get_user(user_id)
    if user:
        return user.model_dump()
    return None


def get_entry(user_id: str, date: str) -> Optional[dict]:
    """Return a single entry for a given user and date, or None if missing."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT date, weight, calories FROM entries
        WHERE user_id = ? AND date = ?
        """,
        (user_id, date),
    )
    row = cur.fetchone()
    conn.close()
    if row:
        return {"date": row[0], "weight": row[1], "calories": row[2]}
    return None
