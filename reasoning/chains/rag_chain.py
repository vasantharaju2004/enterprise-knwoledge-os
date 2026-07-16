from knowledge.retrieval.vector_search import search
from knowledge.retrieval.reranker import rerank
from reasoning.llm_providers.llm_factory import generate_with_fallback
from reasoning.prompts.rag_prompt import build_rag_prompt
from memory.conversation_memory import get_recent_turns, save_turn


def answer_question(
    question: str,
    user_id: str = "dev_user",
    org_id: str = "dev_org",
    document_id: str = None,
    top_k: int = 5,
) -> dict:
    """
    Retrieves relevant chunks ( informed by recent conversation
    context for follow-up questions), reranks them, generates an
    answer , and saves the turn so future questions can reference it.
    """
    recent_turns = get_recent_turns(user_id=user_id, org_id=org_id, limit=3)

    # For retrieval, widen the search query with recent context so
    # a vague follow-up like "which of those " has more to match
    # against than juts its own few words. This is a pragmatic
    # middle ground, not a full query-rewriitng LLM call- cheap,
    # but won't handle every kind of follow-up perfectly.
    search_query = question

    if recent_turns:
        last_turn = recent_turns[-1]
        search_query = f"{last_turn['question']}{last_turn['answer']}{question}"
    candidates = search(
        search_query,
        user_id=user_id,
        org_id=org_id,
        document_id=document_id,
        top_k=top_k,
    )

    if not candidates:
        answer_text = "I don't have any documents to search yet"
        save_turn(question, answer_text, document_id, None, user_id, org_id)
        return {
            "answer": answer_text,
            "sources": [],
            "provider_used": None,
        }
    chunks = rerank(search_query, candidates, top_n=top_k)
    # The LLM prompt uses the ORIGINAL question, not the widened
    # search query - the widened version is only for finidng
    # better chunks , not for confusing the model about what was
    # actually asked this turn.
    history_text = ""
    if recent_turns:
        history_text = "\n\n".join(
            f"Previous Q :{t['question']}\nPrevious A: {t['answer']}"
            for t in recent_turns
        )

    prompt = build_rag_prompt(question, chunks)
    if history_text:
        prompt = f"conversation so far :\n{history_text}\n\n{prompt}"

    result = generate_with_fallback(prompt)

    save_turn(
        question,
        result["answer"],
        document_id,
        result["provider_used"],
        user_id,
        org_id,
    )

    return {
        "answer": result["answer"],
        "sources": [
            {
                "document_id": c["document_id"],
                "chunk_index": c["chunk_index"],
                "rerank_score": c["rerank_score"],
            }
            for c in chunks
        ],
        "provider_used": result["provider_used"],
    }
