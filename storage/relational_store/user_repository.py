import os
import uuid
import psycopg2
from dotenv import load_dotenv
from storage.relational_store.db_connection import get_connection

load_dotenv()

get_connection()

# def get_connection():
#     return psycopg2.connect(
#         host=os.getenv("POSTGRES_HOST"),
#         port=os.getenv("POSTGRES_PORT"),
#         user=os.getenv("POSTGRES_USER"),
#         password=os.getenv("POSTGRES_PASSWORD"),
#         dbname=os.getenv("POSTGRES_DB"),
#     )


def create_auth_tables() -> None:
    """
    creates organisation and users tables. each user belongs to
    exactly one organisation - on registraction, a new personal
    orgainsation is auto-created for them , rarher than requiring
    a seperate "create am org" step.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS organizations(
        id          TEXT PRIMARY KEY,
        name        TEXT NOT NULL,
        created_at  TIMESTAMP DEFAULT NOW()
        )
        """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users(
        id              TEXT PRIMARY KEY,
        org_id          TEXT NOT NULL REFERENCES organizations (id),
        email           TEXT NOT NULL UNIQUE,
        hashed_password TEXT NOT NULL,
        created_at      TIMESTAMP DEFAULT NOW()
        )
        """)
    conn.commit()
    cur.close()
    conn.close()


def create_user(email: str, hashed_password: str) -> dict:
    """
    creates a new organisation and a new user in one call. since
    every user gets thier own personal org on registration. Raises
    if the email already exists - UNIQUE constraint enforces this
    at the database level, not just in application code, so a race
    condition between two simultaneous registrations can't create
    duplicate accounts.
    """
    org_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO organizations (id, name) VALUES (%s, %s)",
        (org_id, f"{email}'s organization"),
    )
    cur.execute(
        " INSERT INTO users ( id, org_id, email, hashed_password) VALUES( %s,%s,%s,%s)",
        (user_id, org_id, email, hashed_password),
    )
    conn.commit()
    cur.close()
    conn.close()

    return {"id": user_id, "org_id": org_id, "email": email}


def get_user_by_email(email: str) -> dict | None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, org_id, email, hashed_password FROM users WHERE email = %s",
        (email,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row is None:
        return None
    return {"id": row[0], "org_id": row[1], "email": row[2], "hashed_password": row[3]}
