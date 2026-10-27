"""Language model client (SDD 8.3): Ollama on the laptop, or deterministic mock templates.

* LLM_MODE=mock: no model needed; agents build their answers from templates (the UI shows a
  "mock" badge).
* LLM_MODE=ollama: LLM_MODEL (fallback LLM_FALLBACK_MODEL) through the Ollama HTTP API. If the
  model is missing or too slow, the call falls back to mock instead of failing, and says so.
Every prompt passes a personal-details check first: the model never receives names, addresses,
IC or phone numbers (NFR-15). A prompt that fails the check is not sent.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass

import httpx

from voltguard import config
from voltguard.agents import scrubber

log = logging.getLogger("voltguard.llm")


class PromptBlocked(Exception):
    pass


@dataclass
class Completion:
    text: str
    mode: str            # ollama | mock
    model: str | None = None
    note: str | None = None


def mode() -> str:
    return config.llm_mode()


def check_prompt(*parts: str) -> None:
    for part in parts:
        found = scrubber.scrub(part).found
        if found:
            raise PromptBlocked(f"prompt held back: it looks like it contains personal details ({', '.join(found)})")


def complete(system: str, user: str, timeout: float | None = None, max_tokens: int = 700) -> Completion | None:
    """Ask the model. Returns None in mock mode or when the model is unavailable (callers then use templates).

    The system prompt is a code constant; the user part carries data (questions, facts, passages) and is
    checked for personal details before anything is sent. PromptBlocked is raised in every mode.
    """
    check_prompt(user)
    if mode() != "ollama":
        return None
    url = os.environ.get("OLLAMA_URL", "http://localhost:11434").rstrip("/")
    timeout = timeout or float(os.environ.get("LLM_TIMEOUT_S", "90"))
    for model in (os.environ.get("LLM_MODEL", "qwen2.5:7b-instruct"), os.environ.get("LLM_FALLBACK_MODEL", "phi3.5")):
        try:
            r = httpx.post(f"{url}/api/chat", timeout=timeout, json={
                "model": model, "stream": False, "options": {"temperature": 0, "num_predict": max_tokens},
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]})
            if r.status_code == 404:
                continue          # model not pulled; try the fallback
            r.raise_for_status()
            return Completion(r.json()["message"]["content"].strip(), "ollama", model)
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            log.warning("LLM call to %s failed (%s); using mock templates", model, exc.__class__.__name__)
            continue
    return None


def available() -> bool:
    if mode() != "ollama":
        return False
    try:
        url = os.environ.get("OLLAMA_URL", "http://localhost:11434").rstrip("/")
        return httpx.get(f"{url}/api/tags", timeout=3).status_code == 200
    except httpx.HTTPError:
        return False
