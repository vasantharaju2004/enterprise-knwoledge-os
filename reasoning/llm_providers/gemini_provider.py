import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def generate(prompt: str) -> str:
    """
    sends a prompt to Gemini and returns the generated text.
    using gemini-2.5-flash - a stable, well established model
    on google's current SDK (google-genai, not the deprecated
    google-generativeai package)
    """
    response = _client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return response.text
