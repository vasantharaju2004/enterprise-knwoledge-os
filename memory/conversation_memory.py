import os
import uuid
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        dbname=os.getenv("POSTGRES_DB"),
    )


def create_conversation_table() -> None:
    """
    Stores every question/answer pair, scoped to user/org, so it
    serves two purposes at once: a reviewable history log, and the
    raw material get_recent_turns() pulls from to give the LLM
    context about what was just discussed.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS conversation_history (
            id             TEXT PRIMARY KEY,
            question       TEXT NOT NULL,
            answer         TEXT NOT NULL,
            document_id    TEXT,
            provider_used  TEXT,
            user_id        TEXT NOT NULL ,
            org_id         TEXT NOT NULL ,
            created_at     TIMESTAMP DEFAULT NOW()
        )
    """)
    conn.commit()
    cur.close()
    conn.close()


def save_turn(
    question: str,
    answer: str,
    user_id: str,
    org_id: str,
    document_id: str,
    provider_used: str,
) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO conversation_history
            (id, question, answer, document_id, provider_used, user_id, org_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            str(uuid.uuid4()),
            question,
            answer,
            document_id,
            provider_used,
            user_id,
            org_id,
        ),
    )
    conn.commit()
    cur.close()
    conn.close()


def get_recent_turns(user_id: str, org_id: str, limit: int = 3) -> list[dict]:
    """
    Returns the most recent turns, oldest first, so they read in
    natural conversational order when injected into a prompt.
    Limited to a small number deliberately — unbounded history
    would quietly inflate every future prompt's token count and
    cost, as flagged back when memory/ was first scoped.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT question, answer FROM conversation_history
        WHERE user_id = %s AND org_id = %s
        ORDER BY created_at DESC
        LIMIT %s
        """,
        (user_id, org_id, limit),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"question": r[0], "answer": r[1]} for r in reversed(rows)]


def get_all_history(user_id: str, org_id: str) -> list[dict]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT question, answer, document_id, provider_used, created_at
        FROM conversation_history
        WHERE user_id = %s AND org_id = %s
        ORDER BY created_at DESC
        """,
        (user_id, org_id),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        {
            "question": r[0],
            "answer": r[1],
            "document_id": r[2],
            "provider_used": r[3],
            "created_at": str(r[4]),
        }
        for r in rows
    ]
