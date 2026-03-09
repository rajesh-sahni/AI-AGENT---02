from typing import Optional

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from ai_agent.routes import router as ai_router
from github_client import create_pull_request, get_branch, get_repo, list_repos
from linear_client import get_issue, list_issues

app = FastAPI()

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ai_router)


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


@app.get("/github/repos/{owner}/{repo}/branch")
def read_github_repo_branch(
    owner: str,
    repo: str,
    branch: Optional[str] = None,
):
    """
    Read the main (default) branch of a specific repo, or a given branch.

    - **owner**: GitHub username or org (e.g. octocat).
    - **repo**: Repository name (e.g. Hello-World).
    - **branch**: Optional. Branch name to read. If omitted, returns the repo's default branch (e.g. main).
    """
    try:
        branch_data = get_branch(owner=owner, repo=repo, branch=branch)
        if branch_data is None:
            raise HTTPException(status_code=404, detail="Repo or branch not found")
        return branch_data
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/github/repos/{owner}/{repo}/{branch}")
def read_github_repo_branch_by_path(owner: str, repo: str, branch: str):
    """
    Read a specific branch of a repo using the branch name in the URL path.

    Example: GET /github/repos/rajesh-sahni/FAQ-AGENt/main
    """
    try:
        branch_data = get_branch(owner=owner, repo=repo, branch=branch)
        if branch_data is None:
            raise HTTPException(status_code=404, detail="Repo or branch not found")
        return branch_data
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/github/repos/{owner}/{repo}/pulls")
def create_github_pull_request(
    owner: str,
    repo: str,
    head: str,
    base: str,
    title: str,
    body: Optional[str] = None,
    draft: bool = False,
    head_repo_owner: Optional[str] = None,
):
    """
    Create a pull request from any branch to any branch.

    - **owner**: Repo owner (e.g. octocat).
    - **repo**: Repo name (e.g. Hello-World).
    - **head**: Source branch (the branch with your changes).
    - **base**: Target branch (the branch you want to merge into).
    - **title**: PR title (required).
    - **body**: Optional PR description.
    - **draft**: If true, create as draft PR.
    - **head_repo_owner**: For forks, pass the fork owner; head sent as owner:branch.
    """
    try:
        result = create_pull_request(
            owner=owner,
            repo=repo,
            head=head,
            base=base,
            title=title,
            body=body,
            draft=draft,
            head_repo_owner=head_repo_owner,
        )
        return {
            "message": "Pull request created successfully",
            "html_url": result.get("html_url"),
            "number": result.get("number"),
        }
    except requests.HTTPError as e:
        detail = str(e)
        if e.response is not None:
            try:
                detail = e.response.json().get("message", str(e))
            except Exception:
                pass
        raise HTTPException(
            status_code=e.response.status_code if e.response else 422, detail=detail
        )
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))