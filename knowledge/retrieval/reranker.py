import cohere
import os
from dotenv import load_dotenv

load_dotenv()

_client = cohere.ClientV2(api_key=os.getenv("COHERE_API_KEY"))


def rerank(query: str, chunks: list[dict], top_n: int = 5) -> list[dict]:
    """ """
    if not chunks:
        return []

    documents = [c["text"] for c in chunks]

    response = _client.rerank(
        model="rerank-v3.5",
        query=query,
        documents=documents,
        top_n=min(top_n, len(chunks)),
    )

    reranked = []

    for result in response.results:
        original_chunk = chunks[result.index]
        reranked.append(
            {
                **original_chunk,
                "rerank_score": result.relevance_score,
            }
        )

    return reranked
