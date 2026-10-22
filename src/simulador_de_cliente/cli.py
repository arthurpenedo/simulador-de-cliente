from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .backends import criar_backend
from .benchmark import rodar
from .personas import PERSONAS
from .rubrica import avaliar_turnos, relatorio
from .simulador import simular, texto_da_conversa
from .sintetico import AtendenteSintetico


def _atendente_humano(historico) -> str:
    print(f"\nCLIENTE: {historico[-1][1]}")
    try:
        return input("VOCÊ (vazio para encerrar): ")
    except EOFError:
        return ""


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="simulador-de-cliente")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("personas", help="lista as personas de cliente")

    t = sub.add_parser("treinar", help="conversa com uma persona e recebe a nota da rubrica")
    t.add_argument("persona", choices=sorted(PERSONAS))
    t.add_argument("--motor", choices=["roteiro", "ollama"], default="roteiro")
    t.add_argument("--modelo", help="modelo do Ollama (padrão qwen2.5:7b)")
    t.add_argument("--auto", choices=["bom", "regular", "ruim"], help="atendente sintético em vez de você")
    t.add_argument("--max-turnos", type=int, default=6)
    t.add_argument("--salvar", help="grava a conversa em JSON")

    a = sub.add_parser("avaliar", help="avalia uma conversa salva (JSON com autor/texto)")
    a.add_argument("arquivo")

    b = sub.add_parser("benchmark", help="mede a rubrica e a mecânica do simulador")
    b.add_argument("--simulacoes", type=int, default=50)
    b.add_argument("--dialogos", type=int, default=300)
    b.add_argument("--semente", type=int, default=42)
    b.add_argument("--saida")

    d = sub.add_parser("demo", help="gera a página HTML de demo (3 conversas simuladas com a nota da rubrica)")
    d.add_argument("--saida", default="site/index.html")
    d.add_argument("--persona", choices=sorted(PERSONAS), default="irritado")

    args = p.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # consoles Windows em cp1252 quebram com "→" e aspas
    if args.cmd == "personas":
        for pe in PERSONAS.values():
            print(f"{pe.id}: {pe.nome}\n  {pe.resumo}")
    elif args.cmd == "treinar":
        persona = PERSONAS[args.persona]
        nivel = {"bom": 2, "regular": 1, "ruim": 0}.get(args.auto)
        atendente = AtendenteSintetico(nivel) if nivel is not None else _atendente_humano
        res = simular(persona, atendente, criar_backend(args.motor, args.modelo), args.max_turnos)
        print("\n" + texto_da_conversa(res, persona))
        print("\n" + relatorio(res.avaliacao))
        if res.problemas_de_papel:
            print("\nFalas do cliente fora do papel: " + "; ".join(res.problemas_de_papel))
        if args.salvar:
            Path(args.salvar).write_text(json.dumps(
                [{"autor": x, "texto": y} for x, y in res.turnos], ensure_ascii=False, indent=2),
                encoding="utf-8")
    elif args.cmd == "avaliar":
        dados = json.loads(Path(args.arquivo).read_text(encoding="utf-8"))
        print(relatorio(avaliar_turnos([d["texto"] for d in dados if d["autor"] == "atendente"])))
    elif args.cmd == "benchmark":
        texto = rodar(args.simulacoes, args.dialogos, args.semente)
        print(texto)
        if args.saida:
            Path(args.saida).write_text(texto + "\n", encoding="utf-8")
    elif args.cmd == "demo":
        from .demo import gerar_html
        saida = Path(args.saida)
        saida.parent.mkdir(parents=True, exist_ok=True)
        saida.write_text(gerar_html(args.persona), encoding="utf-8")
        print(f"página gravada em {saida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
