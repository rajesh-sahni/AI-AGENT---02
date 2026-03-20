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
from github_client import create_pull_request, get_branch, list_repos
from linear_client import list_issues

router = APIRouter(prefix="/ai", tags=["AI Agent"])

STATIC_DIR = Path(__file__).resolve().parent / "static"

# Intent patterns for "create pull request"
GITHUB_PR_INTENT_PATTERNS = [
    # create pull request from dev to main of repo FAQ-AGENt
    r"create\s+pull\s+request\s+from\s+(?P<head>[\w\-/]+)\s+to\s+(?P<base>[\w\-/]+)\s+of\s+repo\s+(?P<repo>[\w\-\.]+)",
    r"create\s+pr\s+from\s+(?P<head>[\w\-/]+)\s+to\s+(?P<base>[\w\-/]+)\s+for\s+(?P<repo>[\w\-\.]+)",
    r"open\s+pull\s+request\s+from\s+(?P<head>[\w\-/]+)\s+to\s+(?P<base>[\w\-/]+)\s+for\s+repo\s+(?P<repo>[\w\-\.]+)",
]


# Intent patterns for "show/list my GitHub repos"
GITHUB_REPOS_INTENT_PATTERNS = [
    r"show\s+(?:me\s+)?(?:all\s+)?(?:my\s+)?(?:github\s+)?repos",
    r"list\s+(?:all\s+)?(?:my\s+)?(?:github\s+)?repos",
    r"(?:all|my)\s+(?:github\s+)?repos(?:itories)?",
    r"repos(?:itories)?\s+(?:of\s+)?(?:my\s+)?(?:github|account)",
    r"(?:my\s+)?github\s+repos(?:itories)?",
    r"get\s+(?:me\s+)?(?:my\s+)?repos(?:itories)?",
]

# Intent patterns for "show/list all Linear issues"
LINEAR_ISSUES_INTENT_PATTERNS = [
    r"show\s+(?:me\s+)?(?:all\s+)?linear\s+issues",
    r"list\s+(?:all\s+)?linear\s+issues",
    r"(?:all\s+)?linear\s+issues",
    r"show\s+(?:me\s+)?issues\s+from\s+linear",
    r"list\s+issues\s+from\s+linear",
]

# Intent patterns for "show (main/dev/any) branch of repo X"
GITHUB_BRANCH_INTENT_PATTERNS = [
    r"show\s+(?:the\s+)?(?P<branch>main|dev|master|develop)\s+branch\s+(?:of\s+)?(?P<repo>[\w\-\.]+)\s*(?:repo(?:sitory)?)?",
    r"(?P<branch>main|dev|master|develop)\s+branch\s+(?:of\s+)?(?P<repo>[\w\-\.]+)",
    r"show\s+branch\s+(?:of\s+)?(?P<repo>[\w\-\.]+)\s*(?:repo(?:sitory)?)?",
    r"branch\s+(?:details?\s+)?(?:of\s+)?(?P<repo>[\w\-\.]+)\s*(?:repo(?:sitory)?)?",
    r"show\s+(?:the\s+)(?P<branch>[\w\-./]+)\s+branch\s+(?:of\s+)?(?P<repo>[\w\-\.]+)\s*(?:repo(?:sitory)?)?",
]

# Intent patterns for "show details of repo X"
GITHUB_REPO_DETAIL_PATTERNS = [
    r"(?:details?|info(?:rmation)?)\s+(?:of|about)\s+repo(?:sitory)?\s+(?P<name>[\w\-\.]+)",
    r"(?:show|display|give|get)\s+(?:me\s+)?(?:the\s+)?details?\s+(?:of\s+)?repo(?:sitory)?\s+(?P<name>[\w\-\.]+)",
    r"repo\s+(?P<name>[\w\-\.]+)\s+details?",
    r"^show\s+(?P<name>[\w\-\.]+)\s+repo$",
    r"^repo\s+(?P<name>[\w\-\.]+)$",
]


def _extract_repo_and_branch(message: str) -> Optional[tuple[str, Optional[str]]]:
    """
    Extract repo name and optional branch name for branch-details intent.

    Examples:
    - "show the main branch of FAQ-AGENt repo" -> ("FAQ-AGENt", "main")
    - "main branch of FAQ-AGENt" -> ("FAQ-AGENt", "main")
    - "show branch of FAQ-AGENt" -> ("FAQ-AGENt", None)  # default branch
    """
    text = message.strip()
    if not text or "branch" not in text.lower():
        return None

    for pattern in GITHUB_BRANCH_INTENT_PATTERNS:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            repo = (match.group("repo") or "").strip().strip("/")
            branch = match.groupdict().get("branch")
            if repo and repo.lower() not in {"repos", "repositories"}:
                return (repo, branch)
    return None


def _extract_pr_request(message: str) -> Optional[tuple[str, str, str]]:
    """
    Extract (repo_name, head, base) for PR creation intent.

    Example:
    - "create pull request from dev to main of repo FAQ-AGENt"
      -> ("FAQ-AGENt", "dev", "main")
    """
    text = message.strip()
    if not text:
        return None
    lowered = text.lower()
    if "pull request" not in lowered and "pr" not in lowered:
        return None

    for pattern in GITHUB_PR_INTENT_PATTERNS:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            head = (match.group("head") or "").strip()
            base = (match.group("base") or "").strip()
            repo = (match.group("repo") or "").strip().strip("/")
            if repo and head and base:
                return repo, head, base

    return None


def _is_github_repos_intent(message: str) -> bool:
    """Check if the user is asking to list their GitHub repositories."""
    text = message.strip().lower()
    for pattern in GITHUB_REPOS_INTENT_PATTERNS:
        if re.search(pattern, text):
            return True
    return False


def _is_linear_issues_intent(message: str) -> bool:
    """Check if the user is asking to list Linear issues."""
    text = message.strip().lower()
    for pattern in LINEAR_ISSUES_INTENT_PATTERNS:
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


def _format_branch_details(branch_data: dict[str, Any], repo_full_name: str) -> str:
    """Format GitHub branch data for chat output."""
    name = branch_data.get("name", "unknown")
    protected = branch_data.get("protected", False)
    commit = branch_data.get("commit", {}) or {}
    sha = commit.get("sha", "unknown")[:7]
    commit_msg = (commit.get("commit", {}) or {}).get("message", "No message")
    commit_msg_first_line = commit_msg.split("\n")[0] if commit_msg else "No message"
    author = (commit.get("commit", {}) or {}).get("author", {}) or {}
    author_name = author.get("name", "unknown")
    date = author.get("date", "unknown")

    lines = [
        f"Branch: {name} (in {repo_full_name})",
        f"Protected: {protected}",
        f"Latest commit: {sha}",
        f"Commit message: {commit_msg_first_line}",
        f"Author: {author_name}",
        f"Date: {date}",
    ]
    return "\n".join(lines)


def _format_linear_issues_response(issues_data: dict[str, Any]) -> str:
    """Format Linear issues list into a readable chat message."""
    nodes = issues_data.get("nodes", []) or []
    page_info = issues_data.get("pageInfo", {}) or {}
    has_next = page_info.get("hasNextPage", False)

    if not nodes:
        return "You don't have any Linear issues yet."

    lines = ["Here are your Linear issues:\n"]
    for i, issue in enumerate(nodes, 1):
        identifier = issue.get("identifier", "UNKNOWN")
        title = issue.get("title", "Untitled")
        state_name = ((issue.get("state") or {}).get("name")) or "Unknown"
        priority = issue.get("priorityLabel") or "No priority"
        assignee_name = ((issue.get("assignee") or {}).get("name")) or "Unassigned"
        url = issue.get("url", "")
        lines.append(
            f"{i}. {identifier}: {title}\n"
            f"   State: {state_name} | Priority: {priority} | Assignee: {assignee_name}\n"
            f"   {url}"
        )

    if has_next:
        lines.append("\n(More Linear issues available.)")
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
    - "show all linear issues" -> lists all issues from Linear
    """
    message = request.message.strip()

    # Intent: create pull request
    pr_request = _extract_pr_request(message)
    if pr_request:
        repo_name, head, base = pr_request
        try:
            repo = _find_repo_by_name(repo_name)
            if repo is None:
                return ChatResponse(
                    message=f"I couldn't find a repository named '{repo_name}' in your GitHub account.",
                    model="github-api",
                    done=True,
                )
            owner = (repo.get("owner") or {}).get("login", "")
            if not owner:
                return ChatResponse(
                    message=f"Could not determine the owner of repository '{repo_name}'.",
                    model="github-api",
                    done=True,
                )
            repo_short_name = repo.get("name", repo_name)
            title = f"Merge {head} into {base}"
            pr = create_pull_request(
                owner=owner,
                repo=repo_short_name,
                head=head,
                base=base,
                title=title,
            )
            html_url = pr.get("html_url")
            number = pr.get("number")
            success_msg = f"Pull request created successfully: #{number} {title}"
            if html_url:
                success_msg += f"\nURL: {html_url}"
            return ChatResponse(
                message=success_msg,
                model="github-api",
                done=True,
            )
        except requests.HTTPError as e:
            detail = str(e)
            if e.response is not None:
                try:
                    data = e.response.json()
                    detail = data.get("message", detail)
                except Exception:
                    pass
            return ChatResponse(
                message=f"Failed to create pull request: {detail}",
                model="github-api",
                done=True,
            )
        except Exception as e:
            return ChatResponse(
                message=f"Failed to create pull request: {e}",
                model="github-api",
                done=True,
            )

    # Intent: branch details for a specific repo
    repo_branch = _extract_repo_and_branch(message)
    if repo_branch:
        repo_name, branch_name = repo_branch
        try:
            repo = _find_repo_by_name(repo_name)
            if repo is None:
                return ChatResponse(
                    message=f"I couldn't find a repository named '{repo_name}' in your GitHub account.",
                    model="github-api",
                    done=True,
                )
            owner = (repo.get("owner") or {}).get("login", "")
            if not owner:
                return ChatResponse(
                    message=f"Could not determine the owner of repository '{repo_name}'.",
                    model="github-api",
                    done=True,
                )
            full_name = repo.get("full_name") or f"{owner}/{repo_name}"
            branch_data = get_branch(owner=owner, repo=repo.get("name", repo_name), branch=branch_name)
            if branch_data is None:
                return ChatResponse(
                    message=f"Branch '{branch_name or 'default'}' not found in {full_name}.",
                    model="github-api",
                    done=True,
                )
            formatted = _format_branch_details(branch_data, full_name)
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

    # Intent: list Linear issues
    if _is_linear_issues_intent(message):
        try:
            issues_data = list_issues(first=50)
            formatted = _format_linear_issues_response(issues_data)
            return ChatResponse(message=formatted, model="linear-api", done=True)
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
        except RuntimeError as e:
            raise HTTPException(status_code=502, detail=str(e))
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
