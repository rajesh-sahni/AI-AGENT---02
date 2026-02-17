# AI Agent

FastAPI app to read Linear issues and GitHub repos.

## Setup

```bash
python -m venv venv #Windows: It is used to create envoirnment
venv\Scripts\activate   # Windows: It is used for command prompt to activate envoirnment

source venv/Scripts/activate #Windows: It is user for git bash to activate envoirnment

pip install -r requirements.txt
```

Create a `.env` in the project root:

```
LINEAR_API_KEY=your_linear_api_key
GITHUB_TOKEN=your_github_personal_access_token
```

## Run

```bash
uvicorn app:app --reload
```

API: `http://localhost:8000`

## API

**Linear**

- List issues: `GET http://localhost:8000/linear/issues`
- Get issue: `GET http://localhost:8000/linear/issues/{issue_id}`

**GitHub**

- List repos: `GET http://localhost:8000/github/repos` (your repos) or `GET http://localhost:8000/github/repos?owner=username`
- Get repo: `GET http://localhost:8000/github/repos/{owner}/{repo}`

- Read branch: `GET http://localhost:8000/github/repos/{owner}/{repo}/{branch}` (e.g. `.../rajesh-sahni/FAQ-AGENt/main`) or `GET http://localhost:8000/github/repos/{owner}/{repo}/branch?branch=main`
