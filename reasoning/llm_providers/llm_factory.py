from reasoning.llm_providers.cohere_provider import generate as cohere_generate
from reasoning.llm_providers.gemini_provider import generate as gemini_generate
from reasoning.llm_providers.groq_provider import generate as groq_generate
from reasoning.llm_providers.local_provider import generate as local_generate


# Priority order : try the best /paid- quality options first, fall through
# to the next on faliure, ending with local - which can't run out.

PROVIDERS = [
    ("cohere", cohere_generate),
    ("gemini", gemini_generate),
    ("groq", groq_generate),
    ("local", local_generate),
]


def generate_with_fallback(prompt: str) -> dict:
    """ """
    for name, func in PROVIDERS:
        try:
            text = func(prompt)
            return {"answer": text, "provider_used": name}
        except Exception as e:
            print(f"[llm_factory]{name} failed: {type(e).__name__}: {e}")
            continue

    raise RuntimeError("All LLM providers failed, including local fallback")
