from knowledge.retrieval.vector_search import search
from reasoning.llm_providers.cohere_provider import generate
from reasoning.prompts.rag_prompt import build_rag_prompt


def answer_question(
    question: str, user_id: str = "dev_user", org_id: str = "dev_org", top_k: int = 5
) -> dict:
    """
    Runs the full question-to-answer journey: retrieve relevant
    chunks scoped to this user/org, build a prompt grounding
    the LLm in those chunks, and generate the final answer.
    """
    chunks = search(question, user_id=user_id, org_id=org_id, top_k=top_k)
    if not chunks:
        return {
            "answer": "I don't have any documents to search yet",
            "sources": [],
        }

    prompt = build_rag_prompt(question, chunks)
    answer_text = generate(prompt)

    return {
        "answer": answer_text,
        "sources": [
            {"document_id": c["document_id"], "chunk_index": c["chunk_index"]}
            for c in chunks
        ],
    }
