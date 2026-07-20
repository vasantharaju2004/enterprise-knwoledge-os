from knowledge.retrieval.vector_search import search
from knowledge.retrieval.reranker import rerank
from reasoning.llm_providers.llm_factory import generate_with_fallback
from reasoning.prompts.rag_prompt import build_rag_prompt
from memory.conversation_memory import get_recent_turns, save_turn
from storage.cache_store.redis_cache import get_cached_answer, set_cached_answer


def answer_question(
    question: str, user_id: str, org_id: str, document_id: str = None, top_k: int = 5
) -> dict:
    """
    Checks the cache first, scoped to this exact user/org/document.
    On a hit, returns instantly with zero LLM calls spent. On a
    miss, runs the full pipeline and caches the result for next time.
    """
    cached = get_cached_answer(question, user_id, org_id, document_id)
    if cached is not None:
        # Still save the turn to conversation history, even on a
        # cache hit — the user genuinely asked this question again,
        # and their history should reflect that.
        save_turn(
            question=question,
            answer=cached["answer"],
            document_id=document_id,
            provider_used=cached.get("provider_used"),
            user_id=user_id,
            org_id=org_id,
        )
        return {**cached, "from_cache": True}

    recent_turns = get_recent_turns(user_id=user_id, org_id=org_id, limit=3)

    search_query = question
    if recent_turns:
        last_turn = recent_turns[-1]
        search_query = f"{last_turn['question']} {last_turn['answer']} {question}"

    candidates = search(
        search_query, user_id=user_id, org_id=org_id, document_id=document_id, top_k=15
    )

    if not candidates:
        answer_text = "I don't have any documents to search yet"
        save_turn(
            question=question,
            answer=answer_text,
            user_id=user_id,
            org_id=org_id,
            document_id=document_id,
            provider_used=None,
        )
        return {
            "answer": answer_text,
            "sources": [],
            "provider_used": None,
            "from_cache": False,
        }

    chunks = rerank(search_query, candidates, top_n=top_k)

    history_text = ""
    if recent_turns:
        history_text = "\n\n".join(
            f"Previous Q: {t['question']}\nPrevious A: {t['answer']}"
            for t in recent_turns
        )

    prompt = build_rag_prompt(question, chunks)
    if history_text:
        prompt = f"Conversation so far:\n{history_text}\n\n{prompt}"

    result = generate_with_fallback(prompt)

    response = {
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

    set_cached_answer(question, user_id, org_id, response, document_id)
    save_turn(
        question=question,
        answer=result["answer"],
        document_id=document_id,
        provider_used=result["provider_used"],
        user_id=user_id,
        org_id=org_id,
    )

    return {**response, "from_cache": False}
