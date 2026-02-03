import json
from typing import Optional

from fastapi import FastAPI, HTTPException, Request

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


# ---------- GitHub webhook ----------

@app.post("/webhook/github")
@app.get("/webhook/github")
async def github_webhook(request: Request):
    payload = await request.json()
    print("========== GITHUB WEBHOOK RECEIVED ==========")
    print(json.dumps(payload, indent=2))
    print("============================================")
    return {"status": "received"}