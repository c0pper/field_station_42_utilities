from pathlib import Path
import os
import json
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "http://127.0.0.1:1234/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "ollama")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "qwen/qwen3.5-9b")
_raw_extra = json.loads(os.getenv("OPENAI_EXTRA_BODY", "null"))
MODEL_API_PARAMETERS: Optional[dict] = {"extra_body": _raw_extra} if _raw_extra else None
