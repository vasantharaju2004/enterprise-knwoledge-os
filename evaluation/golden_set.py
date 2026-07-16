# Each entry: a real question, the document it should be scoped
# to, and keywords that MUST appear somewhere in a correct answer.
# Keyword checking is deliberately simple and deterministic — no
# extra LLM call needed to judge correctness, which matters given
# how scarce the Cohere trial quota is.

GOLDEN_SET = [
    {
        "question": "What programming languages does this person know?",
        "document_id": "9f9265e4-5f4f-4bf4-82bb-def0fdbee36a",
        "expected_keywords": ["Python", "C++", "JavaScript"],
    },
    {
        "question": "What is this person's CGPA?",
        "document_id": "9f9265e4-5f4f-4bf4-82bb-def0fdbee36a",
        "expected_keywords": ["7.24"],
    },
    {
        "question": "What university does this person attend?",
        "document_id": "9f9265e4-5f4f-4bf4-82bb-def0fdbee36a",
        "expected_keywords": ["NITK", "Karnataka"],
    },
    {
        "question": "How many LeetCode problems has this person solved?",
        "document_id": "9f9265e4-5f4f-4bf4-82bb-def0fdbee36a",
        "expected_keywords": ["90"],
    },
    {
        "question": "What framework was used in the Wanderlust project?",
        "document_id": "9f9265e4-5f4f-4bf4-82bb-def0fdbee36a",
        "expected_keywords": ["Node.js", "Express"],
        "match_mode": "any",
    },
]
