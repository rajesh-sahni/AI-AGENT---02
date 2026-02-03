# AI Agent

FastAPI app with Linear integration and GitHub webhooks.

## Setup 

```bash
python -m venv venv #Windows: It is used to create envoirnment
venv\Scripts\activate   # Windows: It is used for command prompt to activate envoirnment
Source venv\Scripts\activate #Windows: It is user for git bash to activate envoirnment

pip install -r requirements.txt
```

Create a `.env` in the project root:

```
LINEAR_API_KEY=your_linear_api_key
```

## Run

```bash
uvicorn app:app --reload
```

API: `http://localhost:8000`

## API

List Linear Issues: `http://localhost:8000/linear/issues`

Github Webhook: `http://localhost:8000/webhook/github`
