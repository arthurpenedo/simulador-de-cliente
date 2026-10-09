"""Rubrica do atendente: empatia, política e segurança, cada uma de 0 a 2.

Regras explícitas (palavras e expressões), sem modelo: o resultado é explicável e
cada nota vem com a evidência que a causou. Os termos ficam sem acento porque o
texto é normalizado antes da busca.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

DIMENSOES = ("empatia", "politica", "seguranca")

EMPATIA = (
    "entendo", "compreendo", "sinto muito", "lamento", "peco desculpas", "desculpe",
    "imagino", "percebo", "e frustrante", "vou te ajudar", "vou ajudar",
)
CORTESIA = ("por favor", "obrigad", "bom dia", "boa tarde", "boa noite", "com prazer")
HOSTIL = (
    r"\bcalma\b", r"nao e problema meu", r"nao e comigo", r"como eu ja disse", r"\bja falei\b",
    r"(voce|senhor|senhora) tem que", r"problema (seu|do senhor)", r"\bnao sei\b",
    r"nao posso fazer nada", r"isso e simples", r"nao entendeu", r"nao leu",
)

PROMESSA_FORA_DA_REGRA = (
    "garanto o reembolso", "garanto o estorno", "devolvo tudo", "devolvo o valor",
    "libero mesmo assim", "faco uma excecao", "sem precisar confirmar", "sem validar",
    "ja aprovei", "aprovado mesmo fora", "pode ficar tranquilo que vou aprovar",
)
CITA_REGRA = (
    "protocolo", "prazo", "politica", "regulamento", "regra", "abrir um chamado",
    "contestacao", "analise", "norma", "condicoes",
)

SENSIVEL = (
    r"senha", r"token", r"cvv", r"codigo de seguranca", r"codigo de verificacao",
    r"codigo (que )?(chegou|enviado) por sms", r"numero completo do cartao",
)
NEGACAO = re.compile(r"(nunca|jamais|nao|sem|evite)\b[^.?!]{0,40}$")
DADO_DE_TERCEIRO = ("passo o saldo", "informo o saldo do titular", "libero os dados")
VERIFICA = (
    "confirmar seus dados", "validar sua identidade", "confirmar sua identidade",
    "dados cadastrais", "canal oficial", "aplicativo oficial", "app oficial", "site oficial",
    "somente o titular", "apenas o titular", "titular da conta", "nunca peco", "jamais peco",
    "nao pedimos", "nao solicitamos", "verificar seus dados", "confirmar o cadastro",
)

DICAS = {
    "empatia": "Reconheça o sentimento antes de resolver (ex.: \"entendo como isso é frustrante\") e evite frases que culpam o cliente.",
    "politica": "Cite a regra e o próximo passo (protocolo, prazo) e não prometa o que a política não permite.",
    "seguranca": "Nunca peça senha, token ou CVV nem passe dados do titular a terceiros; valide a identidade e aponte o canal oficial.",
}


def normalizar(texto: str) -> str:
    base = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in base if unicodedata.category(c) != "Mn")


def _sensivel_pedido(t: str) -> str | None:
    """Primeiro termo sensível que aparece sem negação logo antes (\"nunca peço sua senha\" é ok)."""
    for padrao in SENSIVEL:
        for m in re.finditer(padrao, t):
            inicio = max(0, m.start() - 45)
            trecho = t[inicio:m.start()]
            trecho = re.split(r"[.?!]", trecho)[-1]
            if not NEGACAO.search(trecho + " "):
                return m.group(0)
    return None


@dataclass
class Avaliacao:
    notas: dict[str, int]
    evidencias: dict[str, list[str]] = field(default_factory=dict)

    @property
    def total(self) -> int:
        return sum(self.notas.values())

    def dicas(self) -> list[str]:
        return [DICAS[d] for d in DIMENSOES if self.notas[d] < 2]


def avaliar_texto(texto: str) -> Avaliacao:
    t = normalizar(texto)
    ev: dict[str, list[str]] = {d: [] for d in DIMENSOES}

    hostil = [m.group(0) for p in HOSTIL for m in re.finditer(p, t)]
    marcas = [m for m in EMPATIA if m in t]
    corteses = [m for m in CORTESIA if m in t]
    if hostil:
        empatia = 0
        ev["empatia"] = [f"hostil: \"{h}\"" for h in hostil]
    elif marcas:
        empatia = 2
        ev["empatia"] = [f"empatia: \"{m}\"" for m in marcas]
    elif corteses:
        empatia = 1
        ev["empatia"] = [f"só cortesia: \"{m}\"" for m in corteses]
    else:
        empatia = 0

    promessas = [p for p in PROMESSA_FORA_DA_REGRA if p in t]
    citas = [c for c in CITA_REGRA if c in t]
    if promessas:
        politica = 0
        ev["politica"] = [f"promessa fora da regra: \"{p}\"" for p in promessas]
    elif citas:
        politica = 2
        ev["politica"] = [f"cita a regra: \"{c}\"" for c in citas]
    else:
        politica = 1

    pedido = _sensivel_pedido(t)
    terceiros = [d for d in DADO_DE_TERCEIRO if d in t]
    verifica = [v for v in VERIFICA if v in t]
    if pedido or terceiros:
        seguranca = 0
        if pedido:
            ev["seguranca"].append(f"pede dado sensível: \"{pedido}\"")
        ev["seguranca"] += [f"passa dado de terceiro: \"{d}\"" for d in terceiros]
    elif verifica:
        seguranca = 2
        ev["seguranca"] = [f"verificação/canal oficial: \"{v}\"" for v in verifica]
    else:
        seguranca = 1

    return Avaliacao({"empatia": empatia, "politica": politica, "seguranca": seguranca}, ev)


def avaliar_turnos(turnos: list[str]) -> Avaliacao:
    """Nota da conversa inteira: uma violação em qualquer turno derruba a dimensão."""
    return avaliar_texto("\n".join(turnos))


def relatorio(av: Avaliacao) -> str:
    linhas = ["| Dimensão | Nota (0-2) | Evidência |", "|---|---|---|"]
    for d in DIMENSOES:
        linhas.append(f"| {d} | {av.notas[d]} | {'; '.join(av.evidencias[d]) or '-'} |")
    linhas.append(f"\nTotal: {av.total}/6")
    dicas = av.dicas()
    if dicas:
        linhas.append("\nOnde melhorar:")
        linhas += [f"- {d}" for d in dicas]
    return "\n".join(linhas)
