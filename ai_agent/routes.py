"""
FastAPI routes for AI Agent chat.
"""

import re
from pathlib import Path
from typing import Any, Optional

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

# Intent patterns for "show details of repo X"
GITHUB_REPO_DETAIL_PATTERNS = [
    r"(?:details?|info(?:rmation)?)\s+(?:of|about)\s+repo(?:sitory)?\s+(?P<name>[\w\-\.]+)",
    r"(?:show|display|give|get)\s+(?:me\s+)?(?:the\s+)?details?\s+(?:of\s+)?repo(?:sitory)?\s+(?P<name>[\w\-\.]+)",
    r"repo\s+(?P<name>[\w\-\.]+)\s+details?",
    r"^show\s+(?P<name>[\w\-\.]+)\s+repo$",
    r"^repo\s+(?P<name>[\w\-\.]+)$",
]


def _is_github_repos_intent(message: str) -> bool:
    """Check if the user is asking to list their GitHub repositories."""
    text = message.strip().lower()
    for pattern in GITHUB_REPOS_INTENT_PATTERNS:
        if re.search(pattern, text):
            return True
    return False


def _extract_repo_name(message: str) -> Optional[str]:
    """
    Try to extract a single repository name from the user's message.

    Examples that should match:
    - "show details of repo FAQ-AGENt"
    - "repo FAQ-AGENt details"
    - "repo FAQ-AGENt"
    - "show FAQ-AGENt repo"
    """
    text = message.strip()
    if not text:
        return None

    lowered = text.lower()
    # Don't treat "repos" / "repositories" as a single repo name.
    if "repos" in lowered or "repositories" in lowered:
        # these are likely \"all repos\" type queries; handled separately
        return None

    for pattern in GITHUB_REPO_DETAIL_PATTERNS:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            name = match.group("name").strip().strip("/")
            if name and name.lower() not in {"repos", "repositories"}:
                return name

    # Fallback: if the whole message looks like a single repo name token
    simple = text.replace(" ", "")
    if simple and all(ch.isalnum() or ch in {"-", "_", "."} for ch in simple):
        return simple

    return None


def _find_repo_by_name(name: str) -> Optional[dict[str, Any]]:
    """
    Look up a repository by name using the authenticated user's repos.

    Searches a few pages of /user/repos and matches on name or full_name.
    """
    target = name.strip()
    if not target:
        return None
    target_lower = target.casefold()
    page = 1
    # Search up to 3 pages (~300 repos max)
    while page <= 3:
        data = list_repos(per_page=100, page=page)
        nodes = data.get("nodes", []) or []
        for repo in nodes:
            repo_name = (repo.get("name") or "").casefold()
            full_name = (repo.get("full_name") or "").casefold()
            if repo_name == target_lower:
                return repo
            if full_name == target_lower or full_name.endswith("/" + target_lower):
                return repo

        page_info = data.get("pageInfo", {}) or {}
        if not page_info.get("hasNextPage"):
            break
        page += 1

    return None


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


def _format_repo_details(repo: dict[str, Any]) -> str:
    """Format a single GitHub repository's details for chat output."""
    name = repo.get("name", "unknown")
    owner = (repo.get("owner") or {}).get("login", "")
    full_name = repo.get("full_name") or (f"{owner}/{name}" if owner and name else name)
    url = repo.get("html_url", "")
    desc = repo.get("description") or "No description"
    visibility = repo.get("visibility") or ("private" if repo.get("private") else "public")
    lang = repo.get("language") or "unknown"
    default_branch = repo.get("default_branch", "main")
    stars = repo.get("stargazers_count", 0)
    forks = repo.get("forks_count", 0)
    issues = repo.get("open_issues_count", 0)
    created_at = repo.get("created_at", "unknown")
    updated_at = repo.get("updated_at", "unknown")

    lines = [
        f"Repository: {full_name}",
        f"Visibility: {visibility}",
        f"Description: {desc}",
        f"Language: {lang}",
        f"Default branch: {default_branch}",
        f"Stars: {stars} | Forks: {forks} | Open issues: {issues}",
        f"Created at: {created_at}",
        f"Last updated: {updated_at}",
    ]
    if url:
        lines.append(f"URL: {url}")
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

    Supports special intents:
    - "show me all repos of my github" -> lists all repos
    - "show details of repo XYZ" / "repo XYZ details" -> single repo details
    """
    message = request.message.strip()

    # Intent: details for a specific repo
    repo_name = _extract_repo_name(message)
    if repo_name:
        try:
            repo = _find_repo_by_name(repo_name)
            if repo is None:
                not_found_msg = (
                    f"I couldn't find a repository named '{repo_name}' "
                    "in your GitHub account."
                )
                return ChatResponse(
                    message=not_found_msg,
                    model="github-api",
                    done=True,
                )
            formatted_repo = _format_repo_details(repo)
            return ChatResponse(
                message=formatted_repo,
                model="github-api",
                done=True,
            )
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
