"""Atendentes sintéticos com nível conhecido (0, 1 ou 2) por dimensão: base do benchmark.

Os níveis são rótulos por construção. Algumas frases são paráfrases que a rubrica
NÃO cobre de propósito, para o benchmark mostrar erro de verdade.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

from .rubrica import DIMENSOES, avaliar_turnos

FRASES: dict[str, dict[int, tuple[str, ...]]] = {
    "empatia": {
        2: (
            "Entendo como isso é frustrante, sinto muito pelo transtorno.",
            "Compreendo a sua situação e vou te ajudar com isso.",
            "Peço desculpas pelo ocorrido, imagino o quanto isso incomodou.",
            "Lamento que isso tenha acontecido, vamos resolver juntos.",
            "Fico no seu lugar e sei o quanto isso chateia.",  # paráfrase fora da rubrica
        ),
        1: (
            "Bom dia, obrigado por aguardar.",
            "Por favor, me diga o que aconteceu.",
            "Boa tarde, obrigada pelo contato.",
        ),
        0: (
            "Qual é o problema?",
            "Diga.",
            "Isso é simples, o senhor não entendeu.",
            "Calma, não é problema meu.",
            "Como eu já disse, o senhor tem que ligar de novo.",
        ),
    },
    "politica": {
        2: (
            "Conforme a política, vou abrir o protocolo e o prazo de análise é de até 5 dias úteis.",
            "Pela regra da empresa, preciso registrar uma contestação e você recebe o protocolo agora.",
            "Segundo o regulamento, a análise leva alguns dias; vou abrir um chamado.",
        ),
        1: (
            "Vou verificar o que dá para fazer.",
            "Deixa eu olhar aqui no sistema.",
            "Vou encaminhar o seu caso.",
        ),
        0: (
            "Garanto o reembolso integral agora mesmo.",
            "Faço uma exceção, libero mesmo assim.",
            "Já aprovei o estorno, sem precisar confirmar nada.",
            "Devolvo tudo hoje, pode ficar tranquilo.",
            "Pode contar que o dinheiro volta hoje, não importa o que diz a regra.",  # paráfrase com a palavra "regra"
        ),
    },
    "seguranca": {
        2: (
            "Para sua segurança, preciso confirmar seus dados cadastrais antes de seguir.",
            "Só falo com o titular da conta; nunca peço sua senha por aqui.",
            "Use somente o aplicativo oficial; não pedimos senha nem token.",
            "Preciso validar sua identidade primeiro.",
        ),
        1: (
            "Me explique melhor o pedido.",
            "Certo, vou anotar.",
            "Entendi, continuo aqui.",
        ),
        0: (
            "Qual é a sua senha do app?",
            "Me passe o token que chegou por SMS.",
            "Pode me informar o CVV do cartão?",
            "Passo o saldo do titular para o senhor agora.",
            "Me diga os números que aparecem atrás do seu cartão.",  # paráfrase fora da rubrica
        ),
    },
}


@dataclass
class Dialogo:
    turnos: list[str]
    rotulos: dict[str, int]


def montar(niveis: dict[str, int], rng: random.Random, n_turnos: int = 3) -> Dialogo:
    """Cada turno = frase de empatia + (segurança, política, segurança...) no nível pedido."""
    alternado = ("seguranca", "politica")
    turnos = []
    for i in range(n_turnos):
        e = rng.choice(FRASES["empatia"][niveis["empatia"]])
        outra = alternado[i % 2]
        turnos.append(f"{e} {rng.choice(FRASES[outra][niveis[outra]])}")
    return Dialogo(turnos, dict(niveis))


class AtendenteSintetico:
    """Atendente com o mesmo nível nas três dimensões; usado nas simulações automáticas."""

    def __init__(self, nivel: int, semente: int = 0):
        self.nivel, self.rng, self.i = nivel, random.Random(semente), 0
        self._dialogo = montar({d: nivel for d in DIMENSOES}, self.rng, n_turnos=6)

    def __call__(self, historico) -> str:
        fala = self._dialogo.turnos[self.i % len(self._dialogo.turnos)]
        self.i += 1
        return fala


def avaliar_acerto(n_dialogos: int = 300, semente: int = 42) -> dict[str, float]:
    """Exatidão da rubrica por dimensão em diálogos com níveis independentes sorteados."""
    rng = random.Random(semente)
    acertos = {d: 0 for d in DIMENSOES}
    base = {d: 0 for d in DIMENSOES}  # baseline: sempre prever 1
    for _ in range(n_dialogos):
        niveis = {d: rng.choice((0, 1, 2)) for d in DIMENSOES}
        dlg = montar(niveis, rng)
        av = avaliar_turnos(dlg.turnos)
        for d in DIMENSOES:
            acertos[d] += av.notas[d] == niveis[d]
            base[d] += niveis[d] == 1
    out = {d: acertos[d] / n_dialogos for d in DIMENSOES}
    out["media"] = sum(out.values()) / len(DIMENSOES)
    out["baseline"] = sum(base.values()) / (n_dialogos * len(DIMENSOES))
    return out
