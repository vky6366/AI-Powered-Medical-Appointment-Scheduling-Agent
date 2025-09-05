from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# OpenAI model (expects OPENAI_API_KEY in env)
LLM_MODEL = "gpt-4o-mini"
