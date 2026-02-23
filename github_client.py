"""
GitHub API client – fetch repos via REST API.
Uses GITHUB_TOKEN from .env.
"""

import os
from typing import Any, Optional

import requests

from config import GITHUB_API_URL, GITHUB_TOKEN


def _headers() -> dict[str, str]:
    """Build request headers with GitHub token."""
    token = GITHUB_TOKEN or os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN is not set in .env")
    return {
        "Authorization": f"Bearer {token.strip()}",
        "Accept": "application/vnd.github.v3+json",
    }


def _get(path: str, params: Optional[dict[str, Any]] = None) -> Any:
    """Send a GET request to GitHub API and return the JSON response."""
    url = f"{GITHUB_API_URL.rstrip('/')}/{path.lstrip('/')}"
    resp = requests.get(
        url,
        headers=_headers(),
        params=params,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def _post(path: str, json_body: dict[str, Any]) -> Any:
    """Send a POST request to GitHub API and return the JSON response."""
    url = f"{GITHUB_API_URL.rstrip('/')}/{path.lstrip('/')}"
    resp = requests.post(
        url,
        headers=_headers(),
        json=json_body,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def list_repos(
    per_page: int = 50,
    page: int = 1,
    type_filter: Optional[str] = None,
    sort: Optional[str] = None,
    owner: Optional[str] = None,
    org: bool = False,
) -> dict[str, Any]:
    """
    Fetch a page of repos from GitHub.

    - If owner is None: fetches the authenticated user's repos.
    - If owner is set: fetches that user's repos (org=False) or org's repos (org=True).

    :param per_page: Max number of repos per page (default 50, max 100).
    :param page: Page number for pagination.
    :param type_filter: For user repos: "all", "owner", "member". For org: "all", "public", "private".
    :param sort: "created", "updated", "pushed", "full_name".
    :param owner: Optional owner (username or org) to list their repos instead of current user.
    :param org: If True and owner is set, use orgs/{owner}/repos. If False, use users/{owner}/repos.
    :return: Dict with "nodes" (list of repos) and "pageInfo" (hasNextPage, page).
    """
    per_page = min(per_page, 100)
    params: dict[str, Any] = {"per_page": per_page, "page": page}
    if sort:
        params["sort"] = sort
    if type_filter:
        params["type"] = type_filter

    if owner:
        path = f"orgs/{owner}/repos" if org else f"users/{owner}/repos"
    else:
        path = "user/repos"

    data = _get(path, params)

    # GitHub returns a list; normalize to match Linear's shape
    return {
        "nodes": data,
        "pageInfo": {
            "hasNextPage": len(data) == per_page,
            "page": page,
        },
    }


def get_repo(owner: str, repo: str) -> Optional[dict[str, Any]]:
    """
    Fetch a single repo by owner and repo name.

    :param owner: GitHub username or org name.
    :param repo: Repository name.
    :return: Repo dict or None if not found.
    """
    try:
        return _get(f"repos/{owner}/{repo}")
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code == 404:
            return None
        raise


def get_branch(
    owner: str,
    repo: str,
    branch: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    """
    Fetch the main (default) branch of a repo, or a specific branch.

    If branch is None, uses the repo's default branch (e.g. main or master).

    :param owner: GitHub username or org name.
    :param repo: Repository name.
    :param branch: Optional branch name. If omitted, uses the repo's default branch.
    :return: Branch dict (name, commit.sha, protected, etc.) or None if not found.
    """
    if branch is None:
        repo_data = get_repo(owner=owner, repo=repo)
        if repo_data is None:
            return None
        branch = repo_data.get("default_branch") or "main"
    try:
        return _get(f"repos/{owner}/{repo}/branches/{branch}")
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code == 404:
            return None
        raise


def create_pull_request(
    owner: str,
    repo: str,
    head: str,
    base: str,
    title: str,
    body: Optional[str] = None,
    draft: bool = False,
    head_repo_owner: Optional[str] = None,
) -> dict[str, Any]:
    """
    Create a pull request from any branch to any branch.

    :param owner: Repository owner (e.g. octocat).
    :param repo: Repository name (e.g. Hello-World).
    :param head: Source (head) branch name.
    :param base: Target (base) branch name.
    :param title: PR title (required).
    :param body: Optional PR description.
    :param draft: If True, create as draft PR.
    :param head_repo_owner: If the head branch is in a fork, pass the fork owner.
    :return: Created pull request dict from GitHub.
    """
    payload: dict[str, Any] = {
        "title": title,
        "head": f"{head_repo_owner}:{head}" if head_repo_owner else head,
        "base": base,
    }
    if body is not None:
        payload["body"] = body
    if draft:
        payload["draft"] = True
    return _post(f"repos/{owner}/{repo}/pulls", payload)
