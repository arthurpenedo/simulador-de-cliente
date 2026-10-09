from __future__ import annotations

from .backends import RoteiroBackend
from .personas import PERSONAS
from .rubrica import avaliar_texto
from .simulador import simular
from .sintetico import AtendenteSintetico, avaliar_acerto

NIVEIS = {2: "bom", 1: "regular", 0: "ruim"}

# Casos escritos à mão, com a nota esperada, para pegar o que o gerador não pega.
CURADOS = (
    ("Nunca peço sua senha por aqui, só pelo aplicativo oficial.", "seguranca", 2),
    ("Qual é a sua senha?", "seguranca", 0),
    ("Não compartilhe seu token com ninguém, nem comigo.", "seguranca", 1),
    ("Calma, senhor, isso é simples.", "empatia", 0),
    ("Sinto muito pelo transtorno, vou te ajudar.", "empatia", 2),
    ("Garanto o reembolso hoje.", "politica", 0),
    ("Vou abrir o protocolo, o prazo é de 5 dias úteis.", "politica", 2),
    ("Não posso garantir o reembolso, depende da análise.", "politica", 2),
    ("Posso passar o saldo? Preciso antes validar sua identidade.", "seguranca", 2),
    ("Que chato isso ter acontecido contigo.", "empatia", 2),
)


def acerto_curados() -> tuple[int, int, list[str]]:
    certos, falhas = 0, []
    for texto, dim, esperado in CURADOS:
        obtido = avaliar_texto(texto).notas[dim]
        if obtido == esperado:
            certos += 1
        else:
            falhas.append(f"{dim}: esperado {esperado}, obteve {obtido} → \"{texto}\"")
    return certos, len(CURADOS), falhas


def rodar(n_simulacoes: int = 50, n_dialogos: int = 300, semente: int = 42) -> str:
    ac = avaliar_acerto(n_dialogos, semente)
    certos, total, falhas = acerto_curados()
    out = [
        f"## Rubrica vs. rótulo (diálogos sintéticos, n={n_dialogos}, semente {semente})\n",
        "| Dimensão | Acerto da rubrica |", "|---|---|",
    ]
    out += [f"| {d} | {ac[d]:.1%} |" for d in ("empatia", "politica", "seguranca")]
    out += [f"| **média** | **{ac['media']:.1%}** |",
            f"| baseline (sempre nota 1) | {ac['baseline']:.1%} |", ""]
    out += [f"## Casos escritos à mão: {certos}/{total}\n"]
    out += [f"- {f}" for f in falhas] or ["- sem falhas"]

    out += ["", f"## Simulações automáticas ({n_simulacoes} por persona e nível, cliente por roteiro)\n",
            "| Persona | Atendente | Desfecho bom | Nota média (0-6) | Falas no papel |", "|---|---|---|---|---|"]
    cliente = RoteiroBackend()
    for persona in PERSONAS.values():
        for nivel, nome in NIVEIS.items():
            bons = notas = no_papel_ok = falas = 0
            for s in range(n_simulacoes):
                r = simular(persona, AtendenteSintetico(nivel, semente + s), cliente)
                bons += r.bom
                notas += r.avaliacao.total
                no_papel_ok += r.falas_no_papel
                falas += r.falas_cliente
            out.append(f"| {persona.id} | {nome} | {bons / n_simulacoes:.0%} | "
                       f"{notas / n_simulacoes:.1f} | {no_papel_ok / falas:.0%} |")
    out.append("\nO cliente por roteiro e os atendentes sintéticos vêm do mesmo autor: isto mede a mecânica "
               "(humor, desfecho, rubrica), não o desempenho com atendentes reais nem com um modelo.")
    return "\n".join(out)
