from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from .backends import Backend, Turno
from .personas import Persona, no_papel
from .rubrica import Avaliacao, avaliar_texto, avaliar_turnos

# soma da nota do turno (0-6) -> variação do humor do cliente
DELTA_HUMOR = {0: 2, 1: 2, 2: 1, 3: 0, 4: -1, 5: -2, 6: -2}


@dataclass
class Resultado:
    persona: str
    turnos: list[Turno]
    desfecho: str
    humor_final: int
    avaliacao: Avaliacao
    falas_no_papel: int = 0
    falas_cliente: int = 0
    problemas_de_papel: list[str] = field(default_factory=list)

    @property
    def bom(self) -> bool:
        return self.desfecho == "bom"


def simular(persona: Persona, atendente: Callable[[list[Turno]], str], cliente: Backend,
            max_turnos: int = 6) -> Resultado:
    """Roda a conversa. `atendente` recebe o histórico e devolve a próxima fala (ou "" para encerrar)."""
    humor = persona.humor_inicial
    hist: list[Turno] = [("cliente", persona.abertura)]
    desfecho, falas = "sem desfecho", [persona.abertura]
    ok_papel, problemas = 1, []
    vazou = False

    for i in range(1, max_turnos + 1):
        fala = atendente(hist).strip()
        if not fala:
            desfecho = "atendente encerrou"
            break
        hist.append(("atendente", fala))
        av = avaliar_texto(fala)
        humor = max(0, min(10, humor + DELTA_HUMOR[av.total]))
        if persona.seguranca_critica and av.notas["seguranca"] == 0:
            vazou, desfecho = True, "ruim"
            break
        if humor >= 9:
            desfecho = "ruim"
            break
        if humor <= 2 and i >= 2:
            desfecho = "bom"
        resposta = cliente.responder(persona, hist, humor)
        ok, motivo = no_papel(persona, resposta)
        ok_papel += ok
        if not ok:
            problemas.append(motivo)
        hist.append(("cliente", resposta))
        falas.append(resposta)
        if desfecho == "bom":
            break

    if vazou:
        humor = max(humor, 9)
    textos = [t for a, t in hist if a == "atendente"]
    return Resultado(persona.id, hist, desfecho, humor, avaliar_turnos(textos),
                     ok_papel, len(falas), problemas)


def texto_da_conversa(res: Resultado, persona: Persona) -> str:
    linhas = []
    for autor, texto in res.turnos:
        linhas.append(f"{'CLIENTE' if autor == 'cliente' else 'VOCÊ'}: {texto}")
    rotulo = {"bom": persona.desfecho_bom, "ruim": persona.desfecho_ruim}.get(res.desfecho, res.desfecho)
    linhas.append(f"\nDesfecho: {rotulo} (humor final {res.humor_final}/10)")
    return "\n".join(linhas)
