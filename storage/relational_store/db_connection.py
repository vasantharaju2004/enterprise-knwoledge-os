import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    """
    Single shared connection function_ used by everyday repository
    file instead pf each one defining its own. checks for a cloud
    DATABASE_URL first (Neon, once deployed); falls back to the
    separate host/port/user/password/dbname variables for local
    Docker Postgres. One Place to get this right, not three.
    """
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return psycopg2.connect(database_url)
    else:
        return psycopg2.connect(
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGTRES_PORT"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            dbname=os.getenv("POSTGRES_DB"),
        )
