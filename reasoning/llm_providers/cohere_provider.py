import cohere
import os
from dotenv import load_dotenv

load_dotenv()

_client = cohere.ClientV2(api_key=os.getenv("COHERE_API_KEY"))


def generate(prompt: str) -> str:
    """
    Sends a prompt to Cohere 's command R model and returns the
    generated text. Loaded once as a module-level client, same
    reasoning as the embedding model: aviod reconnectiong on every
    single call.
    """
    response = _client.chat(
        model="command-r-08-2024",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.message.content[0].text
