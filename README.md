# AI Agent

FastAPI app with Linear issues, GitHub repos, and an AI chat agent (Ollama + Llama) like ChatGPT.

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
# OLLAMA_BASE_URL=http://localhost:11434  # optional, default
```

**For AI chat**, install and run [Ollama](https://ollama.com):

```bash
ollama pull llama3.2
ollama serve   # usually runs automatically
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
- Create pull request: `POST http://localhost:8000/github/repos/{owner}/{repo}/pulls?head={source_branch}&base={target_branch}&title={title}`

## Create Pull Request (any branch to any branch)

Create a PR from any source branch to any target branch:

```
POST /github/repos/{owner}/{repo}/pulls?head=feature-branch&base=main&title=My%20PR%20Title
```

Optional query params: `body`, `draft`, `head_repo_owner` (for forks).

### Test steps

1. **Start the server**
   ```bash
   venv\Scripts\activate
   uvicorn app:app --reload
   ```

2. **Ensure you have two branches** in a repo you can push to (e.g. `main` and `feature-xyz`).

3. **Create a PR via curl** (Git Bash or use `curl.exe` in PowerShell):
   ```bash
   curl -X POST "http://localhost:8000/github/repos/YOUR_OWNER/YOUR_REPO/pulls?head=feature-xyz&base=main&title=Test%20PR%20from%20API"
   ```

4. **With body**:
   ```bash
   curl -X POST "http://localhost:8000/github/repos/YOUR_OWNER/YOUR_REPO/pulls?head=feature-xyz&base=main&title=Test%20PR&body=Description%20of%20changes"

   example: curl -X POST "http://localhost:8000/github/repos/rajesh-sahni/FAQ-AGENt/pulls?head=dev&base=main&title=Test%20PR&body=Description%20of%20changes"
   
   ```

5. **PowerShell alternative**:
   ```powershell
   Invoke-RestMethod -Uri "http://localhost:8000/github/repos/YOUR_OWNER/YOUR_REPO/pulls?head=feature-xyz&base=main&title=Test%20PR" -Method POST
   ```

6. **Interactive docs**: Open `http://localhost:8000/docs`, find `POST /github/repos/{owner}/{repo}/pulls`, click "Try it out", enter owner, repo, head, base, title, then "Execute".

---

## AI Agent (Ollama + Llama – ChatGPT-like)

Chat with Llama and other models via Ollama. All AI code lives in `ai_agent/`:

```
ai_agent/
  __init__.py
  schemas.py      # ChatRequest, ChatResponse
  ollama_client.py  # Ollama API client
  routes.py       # FastAPI routes
  static/
    chat.html     # ChatGPT-like UI
```

### Endpoints

- **Chat UI**: `GET http://localhost:8000/ai/chat` – ChatGPT-like web interface
- **List models**: `GET http://localhost:8000/ai/models`
- **Send message (API)**: `POST http://localhost:8000/ai/chat` with JSON body:
  ```json
  {
    "message": "Hello, how are you?",
    "model": "llama3.2",
    "history": [],
    "stream": false
  }
  ```

### Test AI chat

1. Install Ollama and pull a model:
   ```bash
   ollama pull llama3.2
   ```

2. Start the app:
   ```bash
   uvicorn app:app --reload
   ```

3. Open the chat UI: `http://localhost:8000/ai/chat`

4. Or call the API:
   ```bash
   curl -X POST "http://localhost:8000/ai/chat" \
     -H "Content-Type: application/json" \
     -d '{"message":"Hello","model":"llama3.2"}'
   ```
