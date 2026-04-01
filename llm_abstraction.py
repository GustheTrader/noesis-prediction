"""
Sovereign OS — LLM Abstraction Layer

Model-agnostic interface for any LLM backend.
Your model. Your rules. Your sovereignty.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
import json


@dataclass
class LLMResponse:
    """Standardized response from any LLM backend."""
    content: str
    model: str
    backend: str
    tokens_used: int = 0
    latency_ms: float = 0.0


class LLMBackend(ABC):
    """Abstract base for all LLM backends."""

    @abstractmethod
    def complete(self, prompt: str, system: str = "", **kwargs) -> LLMResponse:
        """Generate a completion."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if backend is reachable."""
        ...


class OllamaBackend(LLMBackend):
    """Local Ollama models (llama, mistral, phi, etc.)"""

    def __init__(self, model: str = "llama3", host: str = "http://localhost:11434"):
        self.model = model
        self.host = host

    def complete(self, prompt: str, system: str = "", **kwargs) -> LLMResponse:
        import httpx
        import time

        start = time.time()
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system,
            "stream": False,
        }
        resp = httpx.post(f"{self.host}/api/generate", json=payload, timeout=120)
        data = resp.json()

        return LLMResponse(
            content=data.get("response", ""),
            model=self.model,
            backend="ollama",
            tokens_used=data.get("eval_count", 0),
            latency_ms=(time.time() - start) * 1000,
        )

    def is_available(self) -> bool:
        try:
            import httpx
            resp = httpx.get(f"{self.host}/api/tags", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False


class OpenAIBackend(LLMBackend):
    """OpenAI API (fallback, optional)."""

    def __init__(self, model: str = "gpt-4", api_key: str = ""):
        self.model = model
        self.api_key = api_key

    def complete(self, prompt: str, system: str = "", **kwargs) -> LLMResponse:
        import httpx
        import time

        start = time.time()
        headers = {"Authorization": f"Bearer {self.api_key}"}
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {"model": self.model, "messages": messages}
        resp = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=120,
        )
        data = resp.json()

        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        usage = data.get("usage", {})

        return LLMResponse(
            content=content,
            model=self.model,
            backend="openai",
            tokens_used=usage.get("total_tokens", 0),
            latency_ms=(time.time() - start) * 1000,
        )

    def is_available(self) -> bool:
        return bool(self.api_key)


class AnthropicBackend(LLMBackend):
    """Anthropic Claude API (optional)."""

    def __init__(self, model: str = "claude-sonnet-4-20250514", api_key: str = ""):
        self.model = model
        self.api_key = api_key

    def complete(self, prompt: str, system: str = "", **kwargs) -> LLMResponse:
        import httpx
        import time

        start = time.time()
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            payload["system"] = system

        resp = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=payload,
            timeout=120,
        )
        data = resp.json()

        content = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                content += block.get("text", "")

        return LLMResponse(
            content=content,
            model=self.model,
            backend="anthropic",
            tokens_used=data.get("usage", {}).get("input_tokens", 0)
            + data.get("usage", {}).get("output_tokens", 0),
            latency_ms=(time.time() - start) * 1000,
        )

    def is_available(self) -> bool:
        return bool(self.api_key)


class SovereignLLM:
    """
    Unified interface for any LLM backend.
    
    Supports hot-swapping between backends at runtime.
    Sovereignty = your choice of model, your rules, your data.
    """

    def __init__(self):
        self.backends: dict[str, LLMBackend] = {}
        self.active_backend: Optional[str] = None
        self.fallback_chain: list[str] = []

    def register(self, name: str, backend: LLMBackend):
        """Register a backend."""
        self.backends[name] = backend
        if not self.active_backend:
            self.active_backend = name

    def set_active(self, name: str):
        """Switch active backend."""
        if name in self.backends:
            self.active_backend = name

    def set_fallback(self, chain: list[str]):
        """Set fallback chain: try these in order if primary fails."""
        self.fallback_chain = chain

    def complete(self, prompt: str, system: str = "", **kwargs) -> LLMResponse:
        """Generate completion using active backend (with fallback)."""
        # Try active backend
        backend = self.backends.get(self.active_backend)
        if backend and backend.is_available():
            try:
                return backend.complete(prompt, system, **kwargs)
            except Exception:
                pass

        # Try fallback chain
        for name in self.fallback_chain:
            fb = self.backends.get(name)
            if fb and fb.is_available():
                try:
                    return fb.complete(prompt, system, **kwargs)
                except Exception:
                    continue

        return LLMResponse(
            content="[ERROR: No available LLM backend]",
            model="none",
            backend="none",
        )

    def status(self) -> dict:
        """Status of all backends."""
        return {
            "active": self.active_backend,
            "available": {
                name: backend.is_available()
                for name, backend in self.backends.items()
            },
            "fallback_chain": self.fallback_chain,
        }


# ─── Convenience Setup ─────────────────────────────────────────

def create_sovereign_llm(
    local_model: str = "llama3",
    openai_key: str = "",
    anthropic_key: str = "",
) -> SovereignLLM:
    """
    Create a pre-configured Sovereign LLM.
    
    Priority: Local → Anthropic → OpenAI
    """
    llm = SovereignLLM()

    # Always register local (sovereignty first)
    llm.register("local", OllamaBackend(model=local_model))

    # Optional cloud backends
    if anthropic_key:
        llm.register("anthropic", AnthropicBackend(api_key=anthropic_key))
    if openai_key:
        llm.register("openai", OpenAIBackend(api_key=openai_key))

    # Set fallback chain
    fallback = []
    if anthropic_key:
        fallback.append("anthropic")
    if openai_key:
        fallback.append("openai")
    llm.set_fallback(fallback)

    return llm
