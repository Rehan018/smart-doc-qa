import requests
from openai import OpenAI

from app.core.config import settings


class LLMService:
    def generate(self, prompt: str) -> str:
        if settings.LLM_PROVIDER == "ollama":
            return self._ollama_call(prompt)
        if settings.LLM_PROVIDER == "openai":
            return self._openai_call(prompt)
        raise ValueError("Unsupported LLM provider")

    def _ollama_call(self, prompt: str) -> str:
        response = requests.post(
            f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/generate",
            json={
                "model": settings.OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0},
            },
            timeout=60,
        )

        if response.status_code != 200:
            raise Exception(f"Ollama request failed: {response.text}")

        return response.json().get("response", "").strip()

    def _openai_call(self, prompt: str) -> str:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )

        return (resp.choices[0].message.content or "").strip()
