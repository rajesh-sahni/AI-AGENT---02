# AI Agent

FastAPI app with Linear issues, GitHub repos, and an AI chat agent (Ollama + DeepSeek) like ChatGPT.

## Setup

```bash
venv\Scripts\activate   # Windows: It is used for command prompt to activate envoirnment

source venv/Scripts/activate #Windows: It is user for git bash to activate envoirnment

pip install -r requirements.txt
```

Create a `.env` in the project root:

```
LINEAR_API_KEY=your_linear_api_key
GITHUB_TOKEN=your_github_personal_access_token
GITHUB_REPO_OWNER = your_github_username
GITHUB_REPO_NAME = AI AGENT - 02
# OLLAMA_BASE_URL=http://localhost:11434  # optional, default
```

**For AI chat**, install and run [Ollama](https://ollama.com):

```bash
ollama pull deepseek-r1:1.5b
ollama serve   # usually runs automatically
```

## Run

```bash
uvicorn app:app --reload
```
## API
API: `http://localhost:8000`

**Linear**
- List issues: `GET http://localhost:8000/linear/issues`

**GitHub**

- List repos: `GET http://localhost:8000/github/repos` (your repos) 
or `GET http://localhost:8000/github/repos?owner=username`
example: `GET http://localhost:8000/github/repos?owner=rajesh-sahni`


- Get repo: `GET http://localhost:8000/github/repos/{owner}/{repo}`
example: `GET http://localhost:8000/github/repos/rajesh-sahni/FAQ-AGENt`


- Read branch: `GET http://localhost:8000/github/repos/{owner}/{repo}/{branch}` 
example: `GET http://localhost:8000/github/repos/rajesh-sahni/FAQ-AGENt/main`

or `GET http://localhost:8000/github/repos/{owner}/{repo}/branch?branch=main`
example: `GET http://localhost:8000/github/repos/rajesh-sahni/FAQ-AGENt/branch?branch=main`


- Create pull request: `POST http://localhost:8000/github/repos/{owner}/{repo}/pulls?head={source_branch}&base={target_branch}&title={title}`
example: `POST http://localhost:8000/github/repos/rajesh-sahni/FAQ-AGENt/pulls?head=dev&base=main&title=This is description`


## Create Pull Request (any branch to any branch)
Create a PR from any source branch to any target branch:

```
POST /github/repos/{owner}/{repo}/pulls?head=feature-branch&base=main&title=My%20PR%20Title
```
Optional query params: `body`, `draft`, `head_repo_owner` (for forks).


   ```
**Create a PR via curl** (Git Bash or use `curl.exe` in PowerShell):
   ```bash
   curl -X POST "http://localhost:8000/github/repos/YOUR_OWNER/YOUR_REPO/pulls?head=feature-xyz&base=main&title=Test%20PR%20from%20API"
   ```

**With body**:
   ```bash
   curl -X POST "http://localhost:8000/github/repos/YOUR_OWNER/YOUR_REPO/pulls?head=feature-xyz&base=main&title=Test%20PR&body=Description%20of%20changes"

   example: curl -X POST "http://localhost:8000/github/repos/rajesh-sahni/FAQ-AGENt/pulls?head=dev&base=main&title=Test%20PR&body=Description%20of%20changes"
   
   ```


## AI Agent (Ollama + DeepSeek – ChatGPT-like)

Chat with deepseek model via Ollama. All AI code lives in `ai_agent/`:


### Endpoints

- **Chat UI**: `GET http://localhost:8000/ai/chat` – ChatGPT-like web interface
- **List models**: `GET http://localhost:8000/ai/models`

### Test AI chat
call the API:
   ```bash
   curl -X POST "http://localhost:8000/ai/chat" \
     -H "Content-Type: application/json" \
     -d '{"message":"Hello","model":"llama3.2"}'
   ```
