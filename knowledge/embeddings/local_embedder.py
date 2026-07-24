from sentence_transformers import SentenceTransformer

# Loaded once at import time, not inside the function. Loading a
# model from disk takes real time (a few seconds) — doing it once
# per process startup, not once per embedding call, is what makes
# repeated calls fast after the first one.

# _model = SentenceTransformer("all-MiniLM-L6-v2")
_model = None


def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def embed_texts(
    texts: list[str], input_type: str = "search_document"
) -> list[list[float]]:
    model = _get_model()
    embeddings = model.encode(texts, show_progress_bar=False)
    return embeddings.tolist()


# def embed_texts(texts: list[str]) -> list[list[float]]:
#     """
#     converts a list of chunks into a list of embedding vector
#     Each vector is 384 dimensions - this exact number matters later
#     when we create the Qdrant collection, since it must match exactly

#     Takes a list , not a single string, because embedding many chunks
#     in one batch call is signinficantly faster than calling this once
#     per chunk - the model processes a batch together internally.
#     """
#     embeddings = _model.encode(texts, show_progress_bar=False)
#     return embeddings.tolist()
