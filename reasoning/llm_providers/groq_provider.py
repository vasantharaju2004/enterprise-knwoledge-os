import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def generate(prompt: str) -> str:
    """
    Sends a prompt to Groq's hosted Llama model and returns
    generated text. Groq's free tier has no credit-card requirement
    and generous rate limits, making it a genuie fallback option
    rather than another scarce trial.
    """
    response = _client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )
    return response.choices[0].message.content
