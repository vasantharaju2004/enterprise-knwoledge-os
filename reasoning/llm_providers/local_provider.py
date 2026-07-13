import requests


def generate(prompt: str) -> str:
    """ 
    Sends a prompt to a locally-running Ollama model and returns 
    the generated text. This is the fallback of last resort -
    it never runs out of quota because it's not a hosted API at
    all just a local HTTP call to ollama's own server
    """
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3.2:1b",
            "prompt": prompt,
            "stream": False,
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["response"]
