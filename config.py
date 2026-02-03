import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

LINEAR_API_KEY = os.getenv("LINEAR_API_KEY")
LINEAR_GRAPHQL_URL = "https://api.linear.app/graphql"
