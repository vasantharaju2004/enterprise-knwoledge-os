def build_rag_prompt(question: str, context_chunks: list[dict]) -> str:
    """
    Builds the final prompt sent to the LLm: the retrieved chunks
    as numbered context, followed by strict instructions to answer
    only from that context and say so honestly if the answer isn't
    there - this is what prevents the model from confidently making
    something up when retrieval didn't actually find the answer.
    """
    context_text = "\n\n".join(
        f"[SOURCE {i + 1}]\n{chunk['text']}" for i, chunk in enumerate(context_chunks)
    )
    return f"""Answer the question using ONLY the context below.
    If the context doesnot contain the answer, say "I don't have enough 
    information to When you use information from a source, cite it like [SOURCE 1]
    


Context:
{context_text}

Question: {question}

Answer:"""
