import json
from typing import Any, Dict

from config import LLM_TIMEOUT_SECONDS, OLLAMA_HOST


class OllamaClient(object):
    def __init__(self, model: str, host: str = OLLAMA_HOST):
        self.model = model
        self.host = host.rstrip("/")

    def generate_json(self, prompt: str) -> Dict[str, Any]:
        import requests

        response = requests.post(
            self.host + "/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "format": "json",
            },
            timeout=LLM_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
        content = payload.get("response", "{}")
        return json.loads(content)
