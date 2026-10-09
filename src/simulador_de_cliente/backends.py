"""Quem fala pelo cliente: roteiro determinístico (testes e CI) ou modelo aberto via Ollama."""
from __future__ import annotations

import json
import urllib.request
from typing import Protocol

from .personas import Persona

Turno = tuple[str, str]  # (autor, texto), autor em {"cliente", "atendente"}


class Backend(Protocol):
    def responder(self, persona: Persona, historico: list[Turno], humor: int) -> str: ...


class RoteiroBackend:
    """Escolhe a fala pelo humor atual; sem modelo, sem rede, sempre igual."""

    def responder(self, persona: Persona, historico: list[Turno], humor: int) -> str:
        n = sum(1 for a, _ in historico if a == "cliente")
        if humor <= 2:
            pool = persona.calmas
        elif humor >= 7:
            pool = persona.escalada
        else:
            pool = persona.neutras
        return pool[n % len(pool)]


class OllamaBackend:
    """Usa um modelo local (http://localhost:11434). Gratuito; precisa do Ollama rodando."""

    def __init__(self, modelo: str = "qwen2.5:7b", url: str = "http://localhost:11434", timeout: int = 120):
        self.modelo, self.url, self.timeout = modelo, url.rstrip("/"), timeout

    def responder(self, persona: Persona, historico: list[Turno], humor: int) -> str:
        msgs = [{"role": "system", "content": persona.prompt_sistema(humor)}]
        for autor, texto in historico:
            msgs.append({"role": "assistant" if autor == "cliente" else "user", "content": texto})
        corpo = json.dumps({"model": self.modelo, "messages": msgs, "stream": False}).encode()
        req = urllib.request.Request(f"{self.url}/api/chat", data=corpo,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            return json.loads(r.read().decode())["message"]["content"].strip()


def criar_backend(motor: str, modelo: str | None = None) -> Backend:
    if motor == "roteiro":
        return RoteiroBackend()
    if motor == "ollama":
        return OllamaBackend(modelo) if modelo else OllamaBackend()
    raise ValueError(f"motor desconhecido: {motor}")
