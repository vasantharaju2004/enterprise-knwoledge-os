import os
import cohere
from dotenv import load_dotenv

load_dotenv()

_client = cohere.ClientV2(api_key=os.getenv("COHERE_API_KEY"))


def embed_texts(
    texts: list[str], input_type: str = "search_document"
) -> list[list[float]]:
    """
    Embeds text using Cohere's hosted API instead of a local model —
    used for the deployed backend specifically, where a 512MB RAM
    ceiling makes loading a local model impractical.

    input_type matters: "search_document" when embedding chunks for
    storage, "search_query" when embedding a question at search time.
    Cohere's embed model is asymmetric — using the wrong type doesn't
    error, it just silently produces lower-quality matches.
    """
    response = _client.embed(
        texts=texts,
        model="embed-english-v3.0",
        input_type=input_type,
        embedding_types=["float"],
    )
    return response.embeddings.float_
