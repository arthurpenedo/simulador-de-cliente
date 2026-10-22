"""Página de demo estática: uma conversa simulada por nível de atendente, com a nota e a evidência da rubrica."""
from __future__ import annotations

from html import escape

from .backends import RoteiroBackend
from .benchmark import NIVEIS, rodar_acerto_resumo
from .personas import PERSONAS
from .rubrica import DIMENSOES
from .simulador import simular
from .sintetico import AtendenteSintetico

CSS = (
    "body{font-family:system-ui,sans-serif;max-width:900px;margin:2rem auto;padding:0 1rem}"
    ".conv{border:1px solid #ddd;border-radius:6px;padding:.8rem;margin-bottom:1.2rem}"
    ".cliente{background:#f6f6f6;padding:.4rem .6rem;margin:.3rem 0;border-radius:4px}"
    ".atendente{background:#e8f1fb;padding:.4rem .6rem;margin:.3rem 0;border-radius:4px}"
    "table{border-collapse:collapse;width:100%;font-size:.85rem;margin-top:.6rem}"
    "td,th{border-bottom:1px solid #eee;padding:.25rem;text-align:left}"
    ".n0{color:#b00020;font-weight:600}.n1{color:#8a6d00}.n2{color:#0a6b2d;font-weight:600}"
)


def _conversa(persona_id: str, nivel: int) -> str:
    persona = PERSONAS[persona_id]
    res = simular(persona, AtendenteSintetico(nivel), RoteiroBackend())
    falas = "".join(
        f"<div class='{autor}'><b>{'Cliente' if autor == 'cliente' else 'Atendente'}:</b> {escape(texto)}</div>"
        for autor, texto in res.turnos
    )
    desfecho = {"bom": persona.desfecho_bom, "ruim": persona.desfecho_ruim}.get(res.desfecho, res.desfecho)
    linhas = "".join(
        f"<tr><td>{d}</td><td class='n{res.avaliacao.notas[d]}'>{res.avaliacao.notas[d]}</td>"
        f"<td>{escape('; '.join(res.avaliacao.evidencias[d]) or '-')}</td></tr>"
        for d in DIMENSOES
    )
    return (
        f"<div class='conv'><h3>{escape(persona.nome)}: atendente {NIVEIS[nivel]}</h3>{falas}"
        f"<p><b>Desfecho:</b> {escape(desfecho)} (humor final {res.humor_final}/10)</p>"
        "<table><tr><th>Dimensão</th><th>Nota (0-2)</th><th>Evidência</th></tr>"
        f"{linhas}</table><p>Total: {res.avaliacao.total}/6</p></div>"
    )


def gerar_html(persona_id: str = "irritado") -> str:
    """Três conversas (atendente bom, regular e ruim) com a mesma persona de cliente."""
    blocos = "".join(_conversa(persona_id, nivel) for nivel in (2, 1, 0))
    return (
        "<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'>"
        f"<title>simulador-de-cliente: demo</title><style>{CSS}</style></head><body>"
        "<h1>simulador-de-cliente: demo</h1>"
        "<p>Três conversas <b>simuladas</b> (cliente por roteiro, atendente sintético; nenhum dado real) e a nota "
        "da rubrica de empatia, política e segurança, com a frase que justifica cada nota. "
        f"{rodar_acerto_resumo()} "
        "<a href='https://github.com/arthurpenedo/simulador-de-cliente'>Código no GitHub</a>.</p>"
        f"{blocos}"
        "<p><small>Atendente e cliente vêm do mesmo autor da rubrica: a página mostra a mecânica, "
        "não o desempenho com atendentes reais.</small></p></body></html>"
    )
