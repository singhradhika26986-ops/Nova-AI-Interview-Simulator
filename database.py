import json
import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).with_name("interview_simulator.db")


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'student',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS interviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                topic TEXT NOT NULL,
                average_score REAL NOT NULL,
                recommendation TEXT NOT NULL,
                report_text TEXT NOT NULL,
                rounds_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_token TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS practice_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                topic TEXT NOT NULL,
                question_id TEXT NOT NULL,
                is_bookmarked INTEGER NOT NULL DEFAULT 0,
                is_completed INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, question_id),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )
        connection.commit()


def create_user(full_name, email, password_hash, role="student"):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO users (full_name, email, password_hash, role)
            VALUES (?, ?, ?, ?)
            """,
            (full_name, email.lower().strip(), password_hash, role),
        )
        connection.commit()
        return cursor.lastrowid


def get_user_by_email(email):
    with get_connection() as connection:
        cursor = connection.execute(
            "SELECT * FROM users WHERE email = ?",
            (email.lower().strip(),),
        )
        return cursor.fetchone()


def get_user_by_id(user_id):
    with get_connection() as connection:
        cursor = connection.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,),
        )
        return cursor.fetchone()


def create_user_session(user_id, session_token):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO user_sessions (user_id, session_token)
            VALUES (?, ?)
            """,
            (user_id, session_token),
        )
        connection.commit()
        return cursor.lastrowid


def get_user_by_session_token(session_token):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT users.*
            FROM user_sessions
            JOIN users ON users.id = user_sessions.user_id
            WHERE user_sessions.session_token = ?
            ORDER BY user_sessions.id DESC
            LIMIT 1
            """,
            (session_token,),
        )
        return cursor.fetchone()


def delete_user_session(session_token):
    with get_connection() as connection:
        connection.execute(
            "DELETE FROM user_sessions WHERE session_token = ?",
            (session_token,),
        )
        connection.commit()


def save_interview(user_id, topic, average_score, recommendation, report_text, rounds):
    rounds_json = json.dumps(rounds)
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO interviews (user_id, topic, average_score, recommendation, report_text, rounds_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, topic, average_score, recommendation, report_text, rounds_json),
        )
        connection.commit()
        return cursor.lastrowid


def list_user_interviews(user_id):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT id, topic, average_score, recommendation, report_text, rounds_json, created_at
            FROM interviews
            WHERE user_id = ?
            ORDER BY datetime(created_at) DESC, id DESC
            """,
            (user_id,),
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def list_recent_interviews(limit=10):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT interviews.id, users.full_name, users.email, interviews.topic,
                   interviews.average_score, interviews.recommendation, interviews.created_at,
                   interviews.rounds_json
            FROM interviews
            JOIN users ON users.id = interviews.user_id
            ORDER BY datetime(interviews.created_at) DESC, interviews.id DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_admin_summary():
    with get_connection() as connection:
        total_users = connection.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        total_students = connection.execute(
            "SELECT COUNT(*) FROM users WHERE role = 'student'"
        ).fetchone()[0]
        total_interviews = connection.execute("SELECT COUNT(*) FROM interviews").fetchone()[0]
        avg_score = connection.execute(
            "SELECT COALESCE(ROUND(AVG(average_score), 1), 0) FROM interviews"
        ).fetchone()[0]

        topic_rows = connection.execute(
            """
            SELECT topic, COUNT(*) AS interview_count, ROUND(AVG(average_score), 1) AS avg_score
            FROM interviews
            GROUP BY topic
            ORDER BY interview_count DESC, avg_score DESC
            """
        ).fetchall()

        weak_topic_rows = connection.execute(
            """
            SELECT topic, ROUND(AVG(average_score), 1) AS avg_score
            FROM interviews
            GROUP BY topic
            ORDER BY avg_score ASC, topic ASC
            LIMIT 5
            """
        ).fetchall()

    return {
        "total_users": total_users,
        "total_students": total_students,
        "total_interviews": total_interviews,
        "average_score": avg_score,
        "topic_breakdown": [dict(row) for row in topic_rows],
        "weak_topics": [dict(row) for row in weak_topic_rows],
    }


def upsert_practice_progress(user_id, topic, question_id, is_bookmarked=None, is_completed=None):
    with get_connection() as connection:
        existing = connection.execute(
            """
            SELECT is_bookmarked, is_completed
            FROM practice_progress
            WHERE user_id = ? AND question_id = ?
            """,
            (user_id, question_id),
        ).fetchone()

        bookmark_value = int(is_bookmarked) if is_bookmarked is not None else int(existing["is_bookmarked"]) if existing else 0
        completed_value = int(is_completed) if is_completed is not None else int(existing["is_completed"]) if existing else 0

        connection.execute(
            """
            INSERT INTO practice_progress (user_id, topic, question_id, is_bookmarked, is_completed)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, question_id) DO UPDATE SET
                topic = excluded.topic,
                is_bookmarked = excluded.is_bookmarked,
                is_completed = excluded.is_completed,
                updated_at = CURRENT_TIMESTAMP
            """,
            (user_id, topic, question_id, bookmark_value, completed_value),
        )
        connection.commit()


def get_practice_progress(user_id):
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT topic, question_id, is_bookmarked, is_completed
            FROM practice_progress
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchall()
        return [dict(row) for row in rows]
