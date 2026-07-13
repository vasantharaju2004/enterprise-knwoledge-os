from knowledge.retrieval.vector_search import search
from knowledge.retrieval.reranker import rerank
from reasoning.llm_providers.llm_factory import generate_with_fallback
from reasoning.prompts.rag_prompt import build_rag_prompt


def answer_question(
    question: str,
    user_id: str = "dev_user",
    org_id: str = "dev_org",
    document_id: str = None,
    top_k: int = 5,
) -> dict:
    """
    Runs the full question-to-answer journey: retrieve relevant
    chunks scoped to this user/org, reranks them down to the most genuinely relevant few,
    builds a prompt grounding the LLm in those chunks, and generates the final answer.
    """
    candidates = search(
        question, user_id=user_id, org_id=org_id, document_id=document_id, top_k=top_k
    )
    if not candidates:
        return {
            "answer": "I don't have any documents to search yet",
            "sources": [],
            "provider_used": None,
        }
    chunks = rerank(question, candidates, top_n=top_k)
    prompt = build_rag_prompt(question, chunks)
    answer_text = generate_with_fallback(prompt)

    return {
        "answer": answer_text["answer"],
        "sources": [
            {
                "document_id": c["document_id"],
                "chunk_index": c["chunk_index"],
                "rerank_score": c["rerank_score"],
            }
            for c in chunks
        ],
        "provider_used": answer_text["provider_used"],
    }
