"""
Ollama API client – chat with Llama and other models via Ollama.
"""

import os
from typing import Any, Optional

import requests

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_CHAT_TIMEOUT = int(os.getenv("OLLAMA_CHAT_TIMEOUT", "300"))  # seconds (DeepSeek-R1 can be slow)


def _chat_url() -> str:
    return f"{OLLAMA_BASE_URL.rstrip('/')}/api/chat"


def _models_url() -> str:
    return f"{OLLAMA_BASE_URL.rstrip('/')}/api/tags"


def chat(
    message: str,
    model: str = "deepseek-r1:1.5b",
    history: Optional[list[dict[str, str]]] = None,
    stream: bool = False,
) -> dict[str, Any]:
    """
    Send a chat message to Ollama and get the assistant's reply.

    :param message: User message.
    :param model: Model name (e.g. llama3.2, llama2, mistral).
    :param history: Previous messages [{"role": "user"|"assistant", "content": "..."}].
    :param stream: If True, returns generator; if False, returns full response.
    :return: Response dict with message, model, done.
    """
    history = history or []
    messages = [{"role": m["role"], "content": m["content"]} for m in history]
    messages.append({"role": "user", "content": message})

    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": stream,
    }

    resp = requests.post(
        _chat_url(),
        json=payload,
        timeout=OLLAMA_CHAT_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()

    return {
        "message": data.get("message", {}).get("content", ""),
        "model": data.get("model", model),
        "done": data.get("done", True),
    }


def list_models() -> dict[str, Any]:
    """
    List models available in Ollama.

    :return: Dict with models list from Ollama.
    """
    resp = requests.get(_models_url(), timeout=10)
    resp.raise_for_status()
    return resp.json()
