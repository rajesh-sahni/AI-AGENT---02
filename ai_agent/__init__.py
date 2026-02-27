"""
AI Agent module – chat with Ollama (Llama, etc.) like ChatGPT.
"""

from ai_agent.ollama_client import chat, list_models
from ai_agent.schemas import ChatMessage, ChatRequest, ChatResponse

__all__ = [
    "chat",
    "list_models",
    "ChatMessage",
    "ChatRequest",
    "ChatResponse",
]
