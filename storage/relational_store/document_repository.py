import os
import psycopg2
from dotenv import load_dotenv
import uuid
from storage.relational_store.db_connection import get_connection

load_dotenv()

get_connection()
# def get_connection():
#     """
#     Returns a fresh Postgres connection using .env credentials.
#     called at the start of every reposiotry function - not shaed
#     across requests , which aviods connection state bugs.
#     """

#     return psycopg2.connect(
#         host=os.getenv("POSTGRES_HOST"),
#         port=os.getenv("POSTGTRES_PORT"),
#         user=os.getenv("POSTGRES_USER"),
#         password=os.getenv("POSTGRES_PASSWORD"),
#         dbname=os.getenv("POSTGRES_DB"),
#    )


def create_documents_table() -> None:
    """
    Creates the documents table if it doesn't exist yet.

    source_type distinguishes pdf / docx / image / audio / video / url
    so one table can describe any input modality without assuming
    every document has pages. Modality-specific fields (page_count,
    duration_seconds) stay nullable — only the relevant one gets set.

    user_id / org_id default to placeholder values because no real
    auth exists yet (Phase 14). Plain TEXT, not a foreign key to a
    users/organizations table that doesn't exist yet — building that
    table now would be infrastructure with nothing to point at.
    """

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id                  TEXT PRIMARY KEY,

            filename            TEXT NOT NULL,
            file_path           TEXT,

            source_type         TEXT NOT NULL DEFAULT 'pdf',
            source_url          TEXT,
            duration_seconds    FLOAT,
            page_count          INTEGER,
            status              TEXT NOT NULL DEFAULT 'uploaded',
            user_id             TEXT NOT NULL,
            org_id              TEXT NOT NULL,
            created_at          TIMESTAMP NULL DEFAULT NOW()
            
        )
    """)
    conn.commit()
    cur.close()
    conn.close()


# validate the document metadata
def create_document_record(
    filename: str,
    user_id: str,
    org_id: str,
    source_type: str = "pdf",
    file_path: str = None,
    source_url: str = None,
) -> str:
    """
    Insert a new  document record and returns its generated ID.

    file_path is used for anything saved to local disk (pdf, docx,
    image, audio, video). source_url is used instead when the input
    is a URL with no local file. Exactly one of the two should be
    set — that split is deliberate, not accidental duplication.

    Status starts as 'uploaded' - will become 'extracted',
    'chunked' , 'embedded' as the pipeline progresses.
    """

    doc_id = str(uuid.uuid4())
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO documents
        (id, filename, source_type, file_path, source_url, status, user_id, org_id)
        VALUES (%s, %s, %s, %s, %s,'uploaded', %s, %s)
        """,
        (doc_id, filename, source_type, file_path, source_url, user_id, org_id),
    )
    conn.commit()
    cur.close()
    conn.close()
    return doc_id


# update the document status
def update_document_status(
    doc_id: str, status: str, page_count: int = None, duration_seconds: float = None
) -> None:
    """
    Updates a document's status and whichever modality-specific
    field applies. Passing None for a field that doesn't apply
    to this document type leaves it correctly empty rather than
    forcing a value that means nothing (e.g. page_count for audio).
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE documents
        SET status =%s, page_count=%s, duration_seconds=%s
        WHERE id = %s
        """,
        (status, page_count, duration_seconds, doc_id),
    )
    conn.commit()
    cur.close()
    conn.close()


def get_all_documents(user_id: str, org_id: str) -> list:
    """ """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
            SELECT id, filename,source_type, status,page_count, duration_seconds ,created_at
            FROM documents
            WHERE org_id =%s AND user_id =%s
            ORDER BY created_at DESC
        """,
        (org_id, user_id),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        {
            "id": r[0],
            "filename": r[1],
            "source_type": r[2],
            "status": r[3],
            "page_count": r[4],
            "duration_seconds": r[5],
            "created_at": r[6],
        }
        for r in rows
    ]


def get_all_db_tables():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            table_name,
            column_name,
            data_type,
            column_default,
            is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position;
    """)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return [
        {
            "table_name": r[0],
            "column_name": r[1],
            "data_type": r[2],
            "column_default": r[3],
            "is_nullable": r[4],
        }
        for r in rows
    ]
