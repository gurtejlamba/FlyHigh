"""LLM inference wrapper supporting Ollama (default) and vLLM backends."""
import logging
import time
from dataclasses import dataclass
from typing import Optional

import requests

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    text: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: float


class LLMClient:
    """Thin REST client over Ollama or vLLM (OpenAI-compatible) endpoints."""

    def __init__(
        self,
        provider: str,
        name: str,
        base_url: str,
        temperature: float = 0.0,
        max_tokens: int = 512,
    ):
        self.provider = provider
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.temperature = temperature
        self.max_tokens = max_tokens

    def generate(self, prompt: str, system: Optional[str] = None) -> LLMResponse:
        if self.provider == "ollama":
            return self._ollama(prompt, system)
        if self.provider == "vllm":
            return self._vllm(prompt, system)
        raise ValueError(f"Unknown provider: {self.provider!r}. Use 'ollama' or 'vllm'.")

    def _ollama(self, prompt: str, system: Optional[str]) -> LLMResponse:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        t0 = time.monotonic()
        resp = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.name,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens,
                    "seed": 42,
                },
            },
            timeout=180,
        )
        resp.raise_for_status()
        data = resp.json()
        latency = (time.monotonic() - t0) * 1000

        text = data["message"]["content"]
        prompt_tokens = data.get("prompt_eval_count", 0)
        completion_tokens = data.get("eval_count", 0)
        logger.debug(
            "ollama | model=%s in=%d out=%d latency=%.0fms",
            self.name, prompt_tokens, completion_tokens, latency,
        )
        return LLMResponse(text, prompt_tokens, completion_tokens, latency)

    def _vllm(self, prompt: str, system: Optional[str]) -> LLMResponse:
        """OpenAI-compatible /v1/chat/completions endpoint used by vLLM."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        t0 = time.monotonic()
        resp = requests.post(
            f"{self.base_url}/v1/chat/completions",
            json={
                "model": self.name,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "seed": 42,
            },
            timeout=180,
        )
        resp.raise_for_status()
        data = resp.json()
        latency = (time.monotonic() - t0) * 1000

        text = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        logger.debug(
            "vllm | model=%s in=%d out=%d latency=%.0fms",
            self.name,
            usage.get("prompt_tokens", 0),
            usage.get("completion_tokens", 0),
            latency,
        )
        return LLMResponse(
            text,
            usage.get("prompt_tokens", 0),
            usage.get("completion_tokens", 0),
            latency,
        )


def from_config(cfg: dict) -> "LLMClient":
    """Build an LLMClient from a loaded YAML config dict."""
    m = cfg["model"]
    return LLMClient(
        provider=m["provider"],
        name=m["name"],
        base_url=m["base_url"],
        temperature=m.get("temperature", 0.0),
        max_tokens=m.get("max_tokens", 512),
    )
