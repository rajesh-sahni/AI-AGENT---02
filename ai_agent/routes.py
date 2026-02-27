"""
FastAPI routes for AI Agent chat.
"""

from pathlib import Path
from typing import Any

import requests
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from ai_agent.ollama_client import chat, list_models
from ai_agent.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/ai", tags=["AI Agent"])

STATIC_DIR = Path(__file__).resolve().parent / "static"


@router.get("/models", response_model=dict[str, Any])
def get_models():
    """
    List Ollama models available for chat.

    Requires Ollama to be running locally with at least one model pulled
    (e.g. ollama pull llama3.2).
    """
    try:
        return list_models()
    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=503,
            detail="Ollama is not running. Start it with: ollama serve",
        )
    except requests.HTTPError as e:
        raise HTTPException(
            status_code=e.response.status_code if e.response else 500,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", response_model=ChatResponse)
def post_chat(request: ChatRequest):
    """
    Send a chat message and get the AI assistant's reply.

    - **message**: Your message.
    - **model**: Ollama model name (default: llama3.2).
    - **history**: Previous messages for context.
    - **stream**: If true, streams response (API returns full for now).
    """
    try:
        history_dicts = [{"role": m.role, "content": m.content} for m in request.history]
        result = chat(
            message=request.message,
            model=request.model,
            history=history_dicts,
            stream=request.stream,
        )
        return ChatResponse(
            message=result["message"],
            model=result["model"],
            done=result["done"],
        )
    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=503,
            detail="Ollama is not running. Start it with: ollama serve",
        )
    except requests.HTTPError as e:
        detail = str(e)
        if e.response is not None:
            try:
                detail = e.response.json().get("error", str(e))
            except Exception:
                pass
        raise HTTPException(
            status_code=e.response.status_code if e.response else 500,
            detail=detail,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat")
def chat_page():
    """Serve the ChatGPT-like chat UI (ChatGPT-like interface)."""
    html_path = STATIC_DIR / "chat.html"
    if html_path.exists():
        return FileResponse(html_path, media_type="text/html")
    raise HTTPException(status_code=404, detail="Chat UI not found")
