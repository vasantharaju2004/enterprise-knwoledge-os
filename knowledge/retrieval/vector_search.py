from knowledge.embeddings.local_embedder import embed_texts

from storage.vector_store.qdrant_store import get_client, COLLECTION_NAME


def search(
    query: str,
    user_id: str,
    org_id: str,
    document_id: str = None,
    top_k: int = 5,
) -> list[dict]:
    """
    Embeds a question with the same model used for chunks, searches
    Qdrant for the closest matching vectors, and returns them scoped
    to the asking user's org_id/user_id -= this filter is the tenancy
    enforcement point flagged as critical in the architecture doc.
    without it, one user;s question could return another user's
    private document chunks.
    """

    query_vector = embed_texts([query])[0]

    must_conditions = [
        {"key": "user_id", "match": {"value": user_id}},
        {"key": "org_id", "match": {"value": org_id}},
    ]
    if document_id:
        must_conditions.append({"key": "document_id", "match": {"value": document_id}})

    client = get_client()
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        query_filter={"must": must_conditions},
        limit=top_k,
    )

    return [
        {
            "text": r.payload["text"],
            "document_id": r.payload["document_id"],
            "chunk_index": r.payload["chunk_index"],
            "score": r.score,
        }
        for r in results.points
    ]
