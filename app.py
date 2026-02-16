from typing import Optional

from fastapi import FastAPI, HTTPException

from github_client import get_repo, list_repos
from linear_client import get_issue, list_issues

app = FastAPI()


@app.get("/")
def health():
    return {"status": "Agent running"}


# ---------- Linear issues ----------

@app.get("/linear/issues")
def read_linear_issues(
    first: int = 50,
    after: Optional[str] = None,
    state: Optional[str] = None,
):
    """
    List issues from Linear.

    - **first**: Max number of issues (default 50).
    - **after**: Cursor for next page (from previous response pageInfo.endCursor).
    - **state**: Filter by state type: unstarted, started, completed, canceled.
    """
    try:
        result = list_issues(first=first, after=after, state_filter=state)
        return result
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/linear/issues/{issue_id}")
def read_linear_issue(issue_id: str):
    """
    Get a single Linear issue by ID (UUID or identifier e.g. PROJ-123).
    """
    try:
        issue = get_issue(issue_id)
        if issue is None:
            raise HTTPException(status_code=404, detail="Issue not found")
        return issue
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------- GitHub repos ----------

@app.get("/github/repos")
def read_github_repos(
    per_page: int = 50,
    page: int = 1,
    type_filter: Optional[str] = None,
    sort: Optional[str] = None,
    owner: Optional[str] = None,
    org: bool = False,
):
    """
    List repos from GitHub.

    - **per_page**: Max number of repos (default 50, max 100).
    - **page**: Page number for pagination.
    - **type_filter**: For user: "all", "owner", "member". For org: "all", "public", "private".
    - **sort**: "created", "updated", "pushed", "full_name".
    - **owner**: Optional username or org to list their repos. If omitted, uses authenticated user's repos.
    - **org**: If True and owner is set, treat owner as an org name.
    """
    try:
        result = list_repos(
            per_page=per_page,
            page=page,
            type_filter=type_filter,
            sort=sort,
            owner=owner,
            org=org,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/github/repos/{owner}/{repo}")
def read_github_repo(owner: str, repo: str):
    """
    Get a single GitHub repo by owner and repo name (e.g. octocat/Hello-World).
    """
    try:
        repo_data = get_repo(owner=owner, repo=repo)
        if repo_data is None:
            raise HTTPException(status_code=404, detail="Repo not found")
        return repo_data
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))