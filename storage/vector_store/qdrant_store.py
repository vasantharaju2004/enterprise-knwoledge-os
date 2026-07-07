from dotenv import load_dotenv
import os
import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct


load_dotenv()


COLLECTION_NAME = "document_chunks"
VECTOR_SIZE = 384  # must match local_embedder.py's output dimension exactly


def get_client() -> QdrantClient:
    return QdrantClient(
        host=os.getenv("QDRANT_HOST"),
        port=os.getenv("QDRANT_PORT"),
    )


def create_collection() -> None:
    """
    Creates the document_chunks collection if it doesn't exist.
    Safe to call repeatedly at startup, same pattern as
    create_documents_tabel() in Postgres.
    """

    client = get_client()
    existing = [c.name for c in client.get_collections().collections]

    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )


def upsert_chunks(
    document_id,
    chunks: list[str],
    vectors: list[list[float]],
    user_id: str = "dev_user",
    org_id: str = "dev_org",
) -> None:
    """
    Stores each chunk's vector in Qdrant , with metadata attached
    as a payload. user_id/org_id are stored on every single point
    so retrieval can filter by them later - this is the tenancy
    scoping mechanism, enforced at write time, not left as a
    convention to remember at read time.
    """

    client = get_client()
    points = []

    for i, (chunk_text, vector) in enumerate(zip(chunks, vectors)):
        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={
                    "document_id": document_id,
                    "chunk_index": i,
                    "text": chunk_text,
                    "user_id": user_id,
                    "org_id": org_id,
                },
            )
        )

    client.upsert(collection_name=COLLECTION_NAME, points=points)


def count_points() -> int:
    """
    Returns how many chunks are currently stored - a simple
    sanity check we can run after ingestion to confirm
    the write actually happened.
    """
    client = get_client()
    info = client.get_collection(COLLECTION_NAME)
    return info.points_count
