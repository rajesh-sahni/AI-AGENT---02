"""
FastAPI routes for AI Agent chat.
"""

import re
from pathlib import Path
from typing import Any

import requests
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from ai_agent.ollama_client import chat, list_models
from ai_agent.schemas import ChatRequest, ChatResponse
from github_client import list_repos

router = APIRouter(prefix="/ai", tags=["AI Agent"])

STATIC_DIR = Path(__file__).resolve().parent / "static"

# Intent patterns for "show/list my GitHub repos"
GITHUB_REPOS_INTENT_PATTERNS = [
    r"show\s+(?:me\s+)?(?:all\s+)?(?:my\s+)?(?:github\s+)?repos",
    r"list\s+(?:all\s+)?(?:my\s+)?(?:github\s+)?repos",
    r"(?:all|my)\s+(?:github\s+)?repos(?:itories)?",
    r"repos(?:itories)?\s+(?:of\s+)?(?:my\s+)?(?:github|account)",
    r"(?:my\s+)?github\s+repos(?:itories)?",
    r"get\s+(?:me\s+)?(?:my\s+)?repos(?:itories)?",
]


def _is_github_repos_intent(message: str) -> bool:
    """Check if the user is asking to list their GitHub repositories."""
    text = message.strip().lower()
    for pattern in GITHUB_REPOS_INTENT_PATTERNS:
        if re.search(pattern, text):
            return True
    return False


def _format_repos_response(repos_data: dict[str, Any]) -> str:
    """Format GitHub repos data into a readable chat message."""
    nodes = repos_data.get("nodes", [])
    page_info = repos_data.get("pageInfo", {})
    has_next = page_info.get("hasNextPage", False)

    if not nodes:
        return "You don't have any repositories yet."

    lines = ["Here are your GitHub repositories:\n"]
    for i, repo in enumerate(nodes, 1):
        name = repo.get("full_name", repo.get("name", "unknown"))
        url = repo.get("html_url", "")
        desc = repo.get("description") or "No description"
        lang = repo.get("language", "")
        lang_str = f" ({lang})" if lang else ""
        lines.append(f"{i}. {name}{lang_str}\n   {desc}\n   {url}")

    if has_next:
        lines.append("\n(More repositories available.)")
    return "\n".join(lines)


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

    Supports special intents: "show me all repos of my github" fetches
    GitHub repositories via the API and returns them in the chat.
    """
    message = request.message.strip()

    # Intent: list user's GitHub repos
    if _is_github_repos_intent(message):
        try:
            repos_data = list_repos(per_page=50, page=1)
            formatted = _format_repos_response(repos_data)
            return ChatResponse(message=formatted, model="github-api", done=True)
        except ValueError as e:
            raise HTTPException(status_code=500, detail=str(e))
        except requests.HTTPError as e:
            detail = str(e)
            if e.response is not None:
                try:
                    detail = e.response.json().get("message", str(e))
                except Exception:
                    pass
            raise HTTPException(
                status_code=e.response.status_code if e.response else 500,
                detail=detail,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # Default: use Ollama chat
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
