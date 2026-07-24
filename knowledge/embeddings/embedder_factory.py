import os


def get_embedder():
    """
    Returns the embedding function appropriate for this environment.
    Controlled by EMBEDDING_PROVIDER, set explicitly in Render's
    environment variables for the deployed backend — local dev
    needs no .env change at all, since "local" is the default when
    the variable is unset, preserving exactly how this has worked
    all session.
    """
    provider = os.getenv("EMBEDDING_PROVIDER", "local")

    if provider == "cohere":
        from knowledge.embeddings.cohere_embedder import embed_texts

        return embed_texts
    else:
        from knowledge.embeddings.local_embedder import embed_texts

        return embed_texts
